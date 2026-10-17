# -*- coding: utf-8 -*-
"""`setup`, `import-session`, `sessions` and `check` — end to end, no network.

These tests drive the real CLI entry point (``setup_cli.main``) with an
isolated project directory and a fake Telethon client, then assert on the
files that were written and on what was printed.
"""

from pathlib import Path

import pytest

from fakes import AuthorizedClient, FakeClient, install_fake_telethon
from mido import setup_cli

APP_ID = "12345"
API_HASH = "test-api-hash-not-a-real-credential"
BOT_TOKEN = "123456:AA-valid-token"


@pytest.fixture()
def fake_telethon(monkeypatch):
    def install(client_cls=FakeClient):
        return install_fake_telethon(monkeypatch, client_cls)

    return install


@pytest.fixture()
def creds(monkeypatch):
    monkeypatch.setenv("MIDO_SETUP_APP_ID", APP_ID)
    monkeypatch.setenv("MIDO_SETUP_API_HASH", API_HASH)
    monkeypatch.setenv("MIDO_SETUP_BOT_TOKEN", BOT_TOKEN)
    for key in ("MIDO_SETUP_SESSION_FILE", "MIDO_SETUP_PHONE", "MIDO_SETUP_FORCE_LOGIN"):
        monkeypatch.delenv(key, raising=False)
    return APP_ID, API_HASH, BOT_TOKEN


def env_file(project) -> str:
    return (project / ".env").read_text(encoding="utf-8")


class TestSetup:
    def test_reuses_valid_session_without_asking_for_anything(
        self, project, session_factory, fake_telethon, creds, capsys
    ):
        session_factory(project / "data" / "sessions" / "Mido.session")
        fake_telethon(AuthorizedClient)

        assert setup_cli.main(["setup", "--non-interactive"]) == 0

        out = capsys.readouterr().out
        assert "جلسة صالحة" in out
        # no login flow was started for the user account
        assert all(client.received_phone is None for client in AuthorizedClient.instances)
        content = env_file(project)
        assert f"APP_ID={APP_ID}" in content
        assert f"TG_BOT_TOKEN={BOT_TOKEN}" in content
        assert "SESSION_DIR=data/sessions" in content
        assert "SESSION_NAME=Mido" in content
        assert "BOT_SESSION_NAME=ZedTgbot" in content

    def test_returns_error_when_no_session_and_not_interactive(
        self, project, fake_telethon, creds, capsys
    ):
        fake_telethon(AuthorizedClient)
        assert setup_cli.main(["setup", "--non-interactive"]) == 1
        out = capsys.readouterr().out
        assert "لا توجد جلسة صالحة" in out
        assert not (project / ".env").exists()  # nothing half-configured

    def test_unusable_existing_session_triggers_fresh_login(
        self, project, session_factory, fake_telethon, creds, capsys
    ):
        # a structurally valid file that Telegram refuses (e.g. revoked)
        session_factory(project / "data" / "sessions" / "Mido.session")
        fake_telethon(FakeClient)  # never authorized
        assert setup_cli.main(["setup", "--non-interactive"]) == 1
        out = capsys.readouterr().out
        assert "غير صالح" in out or "تسجيل دخول" in out

    def test_imports_an_existing_session_file(
        self, project, tmp_path, session_factory, fake_telethon, creds, monkeypatch, capsys
    ):
        source = session_factory(tmp_path / "other_pc.session")
        monkeypatch.setenv("MIDO_SETUP_SESSION_FILE", str(source))
        fake_telethon(AuthorizedClient)

        assert setup_cli.main(["setup", "--non-interactive"]) == 0

        target = project / "data" / "sessions" / "Mido.session"
        assert target.is_file()
        assert target.read_bytes() == source.read_bytes()
        assert source.is_file()  # the source is never moved/deleted
        assert "استيراد" in capsys.readouterr().out

    def test_migrates_string_session_to_a_file(
        self, project, fake_telethon, creds, monkeypatch, stub_conversion, capsys
    ):
        (project / ".env").write_text("STRING_SESSION=1TEST-STRING-SESSION\n", encoding="utf-8")
        fake_telethon(AuthorizedClient)
        monkeypatch.setattr("builtins.input", lambda prompt="": "")  # accept the defaults

        assert setup_cli.main(["setup"]) == 0

        out = capsys.readouterr().out
        assert "ملف جلسة" in out
        assert (project / "data" / "sessions" / "Mido.session").is_file()

    def test_backs_up_the_previous_env_file(self, project, session_factory, fake_telethon, creds):
        (project / ".env").write_text("APP_ID=old-value\n", encoding="utf-8")
        session_factory(project / "data" / "sessions" / "Mido.session")
        fake_telethon(AuthorizedClient)

        assert setup_cli.main(["setup", "--non-interactive"]) == 0

        backups = list(project.glob(".env.bak-*"))
        assert len(backups) == 1
        assert "APP_ID=old-value" in backups[0].read_text(encoding="utf-8")

    def test_output_never_contains_raw_secrets(
        self, project, session_factory, fake_telethon, monkeypatch, capsys
    ):
        secret_hash = "SENTINEL-API-HASH-VALUE-1234567890"
        secret_token = "1234567890:SENTINEL-BOT-TOKEN"
        monkeypatch.setenv("MIDO_SETUP_APP_ID", APP_ID)
        monkeypatch.setenv("MIDO_SETUP_API_HASH", secret_hash)
        monkeypatch.setenv("MIDO_SETUP_BOT_TOKEN", secret_token)
        session_factory(project / "data" / "sessions" / "Mido.session")

        class TokenClient(AuthorizedClient):
            async def start(self, bot_token=None):
                assert bot_token == secret_token
                self.authorized = True
                return self

        fake_telethon(TokenClient)
        assert setup_cli.main(["setup", "--non-interactive"]) == 0

        out = capsys.readouterr().out
        assert secret_hash not in out
        assert secret_token not in out

    def test_rejects_invalid_bot_token(
        self, project, session_factory, fake_telethon, creds, monkeypatch, capsys
    ):
        session_factory(project / "data" / "sessions" / "Mido.session")
        monkeypatch.setenv("MIDO_SETUP_BOT_TOKEN", "123456:AA-wrong-token")
        fake_telethon(AuthorizedClient)
        assert setup_cli.main(["setup", "--non-interactive"]) == 1
        assert "توكن البوت غير صالح" in capsys.readouterr().out


class TestImportSessionCommand:
    def test_copies_and_verifies(self, project, tmp_path, session_factory, fake_telethon, capsys):
        (project / ".env").write_text(f"APP_ID={APP_ID}\nAPI_HASH={API_HASH}\n", encoding="utf-8")
        source = session_factory(tmp_path / "pc2.session")
        fake_telethon(AuthorizedClient)

        assert setup_cli.main(["import-session", str(source)]) == 0

        assert (project / "data" / "sessions" / "Mido.session").is_file()
        assert "تم استيراد الجلسة" in capsys.readouterr().out

    def test_no_verify_skips_telegram(self, project, tmp_path, session_factory, fake_telethon, capsys):
        source = session_factory(tmp_path / "pc2.session")
        fake_telethon(FakeClient)  # would fail the online check
        assert setup_cli.main(["import-session", str(source), "--no-verify"]) == 0
        assert "تم استيراد الجلسة" in capsys.readouterr().out

    def test_invalid_file_is_refused(self, project, tmp_path, fake_telethon, capsys):
        bad = tmp_path / "bad.session"
        bad.write_text("this is not a session", encoding="utf-8")
        assert setup_cli.main(["import-session", str(bad), "--no-verify"]) == 1
        assert "ليس ملف جلسة" in capsys.readouterr().out


class TestSessionsCommand:
    def test_lists_files_without_printing_secrets(self, project, session_factory, capsys):
        session_factory(project / "data" / "sessions" / "Mido.session")
        assert setup_cli.main(["sessions"]) == 0
        out = capsys.readouterr().out
        assert "Mido.session" in out
        assert "المصدر المستخدم حاليًا" in out


class TestCheckCommand:
    def test_reports_missing_credentials(self, project, capsys):
        assert setup_cli.main(["check"]) == 1
        out = capsys.readouterr().out
        assert "غير مضبوط" in out

    def test_passes_on_a_minimal_complete_project(self, project, session_factory, capsys):
        (project / "zira" / "plugins").mkdir(parents=True)
        (project / "zira" / "plugins" / "one.py").write_text("# plugin\n", encoding="utf-8")
        session_factory(project / "data" / "sessions" / "Mido.session")
        (project / ".env").write_text(
            f"APP_ID={APP_ID}\nAPI_HASH={API_HASH}\nTG_BOT_TOKEN={BOT_TOKEN}\n", encoding="utf-8"
        )
        assert setup_cli.main(["check"]) == 0
        assert "كل الفحوصات الأساسية ناجحة" in capsys.readouterr().out

    def test_json_output_is_machine_readable(self, project, capsys):
        import json

        setup_cli.main(["check", "--json"])
        lines = [line for line in capsys.readouterr().out.splitlines() if line.strip().startswith("{")]
        payload = json.loads(lines[-1])
        assert "ok" in payload and "problems" in payload
