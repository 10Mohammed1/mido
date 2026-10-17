# -*- coding: utf-8 -*-
"""Session discovery, precedence, locking and import/backup rules."""

import os
from pathlib import Path

import pytest

from mido import session as mido_session


class TestSessionPaths:
    def test_default_dir_is_data_sessions(self, project, monkeypatch):
        monkeypatch.delenv("SESSION_DIR", raising=False)
        assert mido_session.resolve_session_dir() == project / "data" / "sessions"

    def test_relative_dir_is_resolved_against_project_root(self, project, monkeypatch):
        monkeypatch.setenv("SESSION_DIR", "custom/place")
        assert mido_session.resolve_session_dir() == project / "custom" / "place"

    def test_absolute_dir_is_kept(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SESSION_DIR", str(tmp_path))
        assert mido_session.resolve_session_dir() == tmp_path

    def test_session_names_are_configurable(self, monkeypatch):
        monkeypatch.setenv("SESSION_NAME", "Other")
        monkeypatch.setenv("BOT_SESSION_NAME", "BotSession")
        assert mido_session.session_name("user") == "Other"
        assert mido_session.session_name("bot") == "BotSession"

    def test_default_names(self, monkeypatch):
        monkeypatch.delenv("SESSION_NAME", raising=False)
        monkeypatch.delenv("BOT_SESSION_NAME", raising=False)
        assert mido_session.session_name("user") == "Mido"
        assert mido_session.session_name("bot") == "ZedTgbot"


class TestLocateSession:
    def test_managed_location_wins(self, project, session_factory):
        session_factory(project / "data" / "sessions" / "Mido.session")
        location = mido_session.locate_session("Mido")
        assert location.legacy is False
        assert location.file == project / "data" / "sessions" / "Mido.session"
        assert location.exists

    def test_legacy_file_next_to_code_is_used(self, project, session_factory):
        # an existing deployment that still keeps Mido.session in the repo root
        session_factory(project / "Mido.session")
        location = mido_session.locate_session("Mido")
        assert location.legacy is True
        assert location.file == project / "Mido.session"

    def test_missing_session_points_at_managed_path(self, project):
        location = mido_session.locate_session("Mido")
        assert location.legacy is False
        assert location.file == project / "data" / "sessions" / "Mido.session"
        assert not location.exists

    def test_describe_has_no_secrets(self, project, session_factory):
        session_factory(project / "data" / "sessions" / "Mido.session")
        text = mido_session.locate_session("Mido").describe()
        assert "Mido.session" in text
        assert "managed" in text


class TestSessionSourcePrecedence:
    @pytest.mark.parametrize(
        "string_session,file_exists,prefer,expected",
        [
            (None, False, None, "file"),
            (None, True, None, "file"),
            ("code", False, None, "string"),
            ("code", True, None, "file"),  # file wins in auto mode
            ("code", True, "string", "string"),
            (None, True, "string", "file"),  # nothing to use as a string
            ("code", False, "file", "file"),
            (None, False, "file", "file"),
            ("code", True, "bogus", "file"),  # invalid mode falls back to auto
        ],
    )
    def test_matrix(self, monkeypatch, string_session, file_exists, prefer, expected):
        monkeypatch.delenv("SESSION_SOURCE", raising=False)
        assert (
            mido_session.session_source(string_session, prefer=prefer, file_exists=file_exists)
            == expected
        )

    def test_env_variable_is_honoured(self, monkeypatch):
        monkeypatch.setenv("SESSION_SOURCE", "string")
        assert mido_session.session_source("code", file_exists=True) == "string"


class TestLocking:
    def test_second_process_is_refused(self, project, session_factory):
        session_factory(project / "data" / "sessions" / "Mido.session")
        location = mido_session.locate_session("Mido")
        lock = mido_session.acquire_session_lock(location)
        try:
            with pytest.raises(mido_session.SessionLockedError) as excinfo:
                mido_session.acquire_session_lock(location)
            assert str(os.getpid()) in str(excinfo.value)
        finally:
            lock.release()
        # once released the session is free again
        again = mido_session.acquire_session_lock(location)
        again.release()

    def test_stale_lock_is_replaced(self, project, session_factory):
        session_factory(project / "data" / "sessions" / "Mido.session")
        location = mido_session.locate_session("Mido")
        lock_file = location.file.with_name(location.file.name + ".lock")
        lock_file.write_text('{"pid": 2147483646, "host": "nowhere"}', encoding="utf-8")
        lock = mido_session.acquire_session_lock(location)
        try:
            assert lock.path == lock_file
            assert str(os.getpid()) in lock_file.read_text(encoding="utf-8")
        finally:
            lock.release()

    def test_env_override_skips_locking(self, project, monkeypatch):
        monkeypatch.setenv("MIDO_IGNORE_SESSION_LOCK", "1")
        location = mido_session.locate_session("Mido")
        lock = mido_session.acquire_session_lock(location)
        assert lock.acquired is False
        assert not lock.path.exists()

    def test_status_reports_running_instance(self, project, session_factory):
        session_factory(project / "data" / "sessions" / "Mido.session")
        location = mido_session.locate_session("Mido")
        lock = mido_session.acquire_session_lock(location)
        try:
            status = mido_session.session_lock_status(location)
            assert status["running"] is True
            assert status["pid"] == os.getpid()
        finally:
            lock.release()


class TestValidation:
    def test_missing_file(self, tmp_path):
        ok, message = mido_session.validate_session_file(tmp_path / "nope.session")
        assert ok is False
        assert "غير موجود" in message

    def test_empty_file(self, tmp_path):
        path = tmp_path / "empty.session"
        path.write_bytes(b"")
        ok, _ = mido_session.validate_session_file(path)
        assert ok is False

    def test_not_a_sqlite_file(self, tmp_path):
        path = tmp_path / "junk.session"
        path.write_text("STRING_SESSION=do-not-use-me", encoding="utf-8")
        ok, message = mido_session.validate_session_file(path)
        assert ok is False
        assert "ليس ملف جلسة" in message or "تالف" in message

    def test_valid_file(self, tmp_path, session_factory):
        path = session_factory(tmp_path / "good.session")
        ok, message = mido_session.validate_session_file(path)
        assert ok is True
        assert message == "ok"


class TestImport:
    def test_import_copies_into_managed_dir(self, project, tmp_path, session_factory):
        source = session_factory(tmp_path / "from_other_pc.session")
        location, backup = mido_session.import_session_file(source, name="Mido")
        assert backup is None
        assert location.file == project / "data" / "sessions" / "Mido.session"
        assert location.file.read_bytes() == source.read_bytes()

    def test_import_refuses_to_overwrite_without_force(self, project, tmp_path, session_factory):
        session_factory(project / "data" / "sessions" / "Mido.session")
        source = session_factory(tmp_path / "new.session")
        with pytest.raises(mido_session.SessionImportError) as excinfo:
            mido_session.import_session_file(source, name="Mido")
        assert "--force" in str(excinfo.value)

    def test_import_with_force_keeps_backup(self, project, tmp_path, session_factory):
        existing = session_factory(project / "data" / "sessions" / "Mido.session", dc_id=2)
        original_bytes = existing.read_bytes()
        source = session_factory(tmp_path / "new.session", dc_id=5)
        location, backup = mido_session.import_session_file(source, name="Mido", force=True)
        assert backup is not None and backup.is_file()
        assert backup.read_bytes() == original_bytes
        assert location.file.read_bytes() == source.read_bytes()

    def test_import_rejects_invalid_source(self, project, tmp_path):
        bad = tmp_path / "bad.session"
        bad.write_text("not a session", encoding="utf-8")
        with pytest.raises(mido_session.SessionImportError):
            mido_session.import_session_file(bad, name="Mido")

    def test_import_of_same_path_is_a_noop(self, project, session_factory):
        same = session_factory(project / "data" / "sessions" / "Mido.session")
        location, backup = mido_session.import_session_file(same, name="Mido")
        assert backup is None
        assert location.file == same

    def test_backup_never_deletes_the_original(self, project, session_factory):
        session_factory(project / "data" / "sessions" / "Mido.session")
        location = mido_session.locate_session("Mido")
        backup = mido_session.backup_session(location)
        assert backup is not None
        assert backup.is_file() and location.file.is_file()
        assert backup.name.startswith("Mido.session.bak-")

    def test_cleanup_partial_session_removes_sidecars(self, project, session_factory):
        session_factory(project / "data" / "sessions" / "Mido.session")
        journal = project / "data" / "sessions" / "Mido.session-journal"
        journal.write_text("partial", encoding="utf-8")
        location = mido_session.locate_session("Mido")
        removed = mido_session.cleanup_partial_session(location)
        assert len(removed) >= 2
        assert not location.file.exists()
        assert not journal.exists()


class TestInventory:
    def test_list_session_files_reports_validity(self, project, session_factory):
        session_factory(project / "data" / "sessions" / "Mido.session")
        (project / "data" / "sessions" / "broken.session").write_text("x", encoding="utf-8")
        entries = mido_session.list_session_files(project / "data" / "sessions")
        by_name = {Path(item["file"]).name: item for item in entries}
        assert by_name["Mido.session"]["valid"] is True
        assert by_name["broken.session"]["valid"] is False
        assert "lock" in by_name["Mido.session"]
