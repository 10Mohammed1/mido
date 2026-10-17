# -*- coding: utf-8 -*-
"""Authentication flows — always against a fake Telethon client (no network).

The fake client implements exactly the API surface ``mido/auth.py`` uses, so
the tests exercise the real control flow: phone → code → two-step password,
retries, flood waits, revoked sessions and bot-token validation.
"""

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
import telethon.errors as terr

from mido import auth as mido_auth

ERROR_NAMES = (
    "AccessTokenExpiredError",
    "AccessTokenInvalidError",
    "ApiIdInvalidError",
    "AuthKeyDuplicatedError",
    "AuthKeyUnregisteredError",
    "FloodWaitError",
    "PasswordHashInvalidError",
    "PhoneCodeExpiredError",
    "PhoneCodeInvalidError",
    "PhoneNumberBannedError",
    "PhoneNumberInvalidError",
    "SessionPasswordNeededError",
    "SessionRevokedError",
    "UserDeactivatedBanError",
    "UserDeactivatedError",
)


def _err(cls, **attrs):
    """Build a real Telethon error instance without a request context."""
    try:
        exc = cls(request=None)
    except TypeError:  # pragma: no cover - defensive
        exc = cls()
    for key, value in attrs.items():
        setattr(exc, key, value)
    return exc


class FakeSession:
    def save(self):
        return "1" + "x" * 120


class FakeClient:
    """Minimal Telethon replacement (no sockets, no files)."""

    instances = []

    def __init__(self, session, api_id, api_hash):
        self.session = FakeSession()
        self.api_id = api_id
        self.api_hash = api_hash
        self.received_phone = None
        self.expected_code = "12345"
        self.expire_next = False
        self.password = "s3cret-pw"
        self.needs_2fa = False
        self.valid_token = "123456:AA-valid-token"
        self.authorized = False
        self.connected = False
        self.disconnected = False
        self.me = SimpleNamespace(first_name="Mido", last_name="Tester", username="mido_tester")
        FakeClient.instances.append(self)

    async def connect(self):
        self.connected = True

    async def disconnect(self):
        self.disconnected = True

    async def is_user_authorized(self):
        return self.authorized

    async def get_me(self):
        return self.me if self.authorized else None

    async def send_code_request(self, phone):
        self.received_phone = phone
        return SimpleNamespace(phone_code_hash="hash-1")

    async def sign_in(self, phone=None, code=None, phone_code_hash=None, password=None):
        if password is not None:
            if password != self.password:
                raise _err(terr.PasswordHashInvalidError)
            self.authorized = True
            return self.me
        if self.expire_next:
            self.expire_next = False
            raise _err(terr.PhoneCodeExpiredError)
        if code != self.expected_code:
            raise _err(terr.PhoneCodeInvalidError)
        if self.needs_2fa:
            raise _err(terr.SessionPasswordNeededError)
        self.authorized = True
        return self.me

    async def start(self, bot_token=None):
        if bot_token != self.valid_token:
            raise _err(terr.AccessTokenInvalidError)
        self.authorized = True
        return self


class AuthorizedClient(FakeClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.authorized = True


class RevokedClient(FakeClient):
    async def is_user_authorized(self):
        raise _err(terr.AuthKeyUnregisteredError)


class UnreachableClient(FakeClient):
    async def connect(self):
        raise ConnectionError("network down")


@pytest.fixture()
def fake_telethon(monkeypatch):
    """Route ``mido.auth`` to the fake client but keep real error classes."""

    def install(client_cls=FakeClient):
        table = {name: getattr(terr, name) for name in ERROR_NAMES}
        table["TelegramClient"] = client_cls
        table["StringSession"] = lambda value="": ("string", value)
        monkeypatch.setattr(mido_auth, "_import_telethon", lambda: table)
        FakeClient.instances = []
        return table

    return install


@pytest.fixture()
def stub_conversion(monkeypatch, tmp_path):
    """Replace the string→file conversion with a placeholder writer."""

    def fake_write(string_session, target_stem):
        stem = Path(str(target_stem))
        path = stem.parent / (stem.name + ".session")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"SQLite format 3\x00fake")
        return str(path)

    monkeypatch.setattr(mido_auth, "write_file_session_from_string", fake_write)
    return fake_write


def run(coro, timeout=30):
    return asyncio.run(asyncio.wait_for(coro, timeout))


class TestInteractiveLogin:
    def test_success_without_2fa(self, fake_telethon, stub_conversion, tmp_path):
        fake_telethon(FakeClient)
        answers = iter(["12345"])
        result = run(
            mido_auth.interactive_login(
                api_id=1,
                api_hash="hash",
                target_stem=tmp_path / "Mido",
                phone="+201234567890",
                ask=lambda prompt: next(answers),
                ask_secret=lambda prompt: "unused",
            )
        )
        assert result.ok is True
        assert result.identifier and "mido_tester" in result.identifier
        assert result.session_file.endswith("Mido.session")
        client = FakeClient.instances[-1]
        assert client.received_phone == "+201234567890"
        assert client.disconnected is True

    def test_prompts_for_phone_when_missing(self, fake_telethon, stub_conversion, tmp_path):
        fake_telethon(FakeClient)
        answers = iter(["+201111111111", "12345"])
        result = run(
            mido_auth.interactive_login(
                api_id=1,
                api_hash="hash",
                target_stem=tmp_path / "Mido",
                ask=lambda prompt: next(answers),
                ask_secret=lambda prompt: "unused",
            )
        )
        assert result.ok is True
        assert FakeClient.instances[-1].received_phone == "+201111111111"

    def test_two_step_only_when_telegram_asks(self, fake_telethon, stub_conversion, tmp_path):
        fake_telethon(FakeClient)
        password_prompts = []

        def ask_secret(prompt):
            password_prompts.append(prompt)
            return "s3cret-pw"

        answers = iter(["12345"])
        result = run(
            mido_auth.interactive_login(
                api_id=1,
                api_hash="hash",
                target_stem=tmp_path / "Mido",
                phone="+201234567890",
                ask=lambda prompt: next(answers),
                ask_secret=ask_secret,
            )
        )
        assert result.ok is True
        assert password_prompts == []  # no needless password prompt

        fake_telethon(FakeClient)

        def client_cls(*args, **kwargs):
            client = FakeClient(*args, **kwargs)
            client.needs_2fa = True
            return client

        mido_auth._import_telethon()["TelegramClient"] = client_cls
        answers = iter(["12345"])
        result = run(
            mido_auth.interactive_login(
                api_id=1,
                api_hash="hash",
                target_stem=tmp_path / "Second",
                phone="+201234567890",
                ask=lambda prompt: next(answers),
                ask_secret=ask_secret,
            )
        )
        assert result.ok is True
        assert len(password_prompts) == 1

    def test_wrong_password_is_retried(self, fake_telethon, stub_conversion, tmp_path):
        fake_telethon(FakeClient)

        def client_cls(*args, **kwargs):
            client = FakeClient(*args, **kwargs)
            client.needs_2fa = True
            return client

        mido_auth._import_telethon()["TelegramClient"] = client_cls
        passwords = iter(["wrong", "s3cret-pw"])
        answers = iter(["12345"])
        result = run(
            mido_auth.interactive_login(
                api_id=1,
                api_hash="hash",
                target_stem=tmp_path / "Mido",
                phone="+201234567890",
                ask=lambda prompt: next(answers),
                ask_secret=lambda prompt: next(passwords),
                max_password_attempts=2,
            )
        )
        assert result.ok is True

    def test_wrong_password_exhausted(self, fake_telethon, stub_conversion, tmp_path):
        fake_telethon(FakeClient)

        def client_cls(*args, **kwargs):
            client = FakeClient(*args, **kwargs)
            client.needs_2fa = True
            return client

        mido_auth._import_telethon()["TelegramClient"] = client_cls
        answers = iter(["12345"])
        with pytest.raises(mido_auth.LoginError) as excinfo:
            run(
                mido_auth.interactive_login(
                    api_id=1,
                    api_hash="hash",
                    target_stem=tmp_path / "Mido",
                    phone="+201234567890",
                    ask=lambda prompt: next(answers),
                    ask_secret=lambda prompt: "always-wrong",
                    max_password_attempts=2,
                )
            )
        assert "كلمة مرور" in str(excinfo.value)

    def test_invalid_code_retried_without_new_request(self, fake_telethon, stub_conversion, tmp_path):
        fake_telethon(FakeClient)
        answers = iter(["00000", "12345"])
        result = run(
            mido_auth.interactive_login(
                api_id=1,
                api_hash="hash",
                target_stem=tmp_path / "Mido",
                phone="+201234567890",
                ask=lambda prompt: next(answers),
                ask_secret=lambda prompt: "unused",
            )
        )
        assert result.ok is True
        assert FakeClient.instances[-1].received_phone == "+201234567890"

    def test_expired_code_requests_a_new_one(self, fake_telethon, stub_conversion, tmp_path):
        fake_telethon(FakeClient)

        def client_cls(*args, **kwargs):
            client = FakeClient(*args, **kwargs)
            client.expire_next = True
            sends = {"count": 0}
            original = client.send_code_request

            async def send_code_request(phone):
                sends["count"] += 1
                return await original(phone)

            client.send_code_request = send_code_request
            client._sends = sends
            return client

        mido_auth._import_telethon()["TelegramClient"] = client_cls
        # 1st code expires → a new one is requested automatically → 2nd code works
        answers = iter(["12345", "12345"])
        result = run(
            mido_auth.interactive_login(
                api_id=1,
                api_hash="hash",
                target_stem=tmp_path / "Mido",
                phone="+201234567890",
                ask=lambda prompt: next(answers),
                ask_secret=lambda prompt: "unused",
            )
        )
        assert result.ok is True
        assert FakeClient.instances[-1]._sends["count"] == 2

    def test_invalid_code_exhausted(self, fake_telethon, stub_conversion, tmp_path):
        fake_telethon(FakeClient)
        answers = iter(["11111", "22222", "33333", "44444"])
        with pytest.raises(mido_auth.LoginError):
            run(
                mido_auth.interactive_login(
                    api_id=1,
                    api_hash="hash",
                    target_stem=tmp_path / "Mido",
                    phone="+201234567890",
                    ask=lambda prompt: next(answers),
                    ask_secret=lambda prompt: "unused",
                    max_code_attempts=3,
                )
            )

    def test_long_flood_wait_is_reported(self, fake_telethon, stub_conversion, tmp_path):
        fake_telethon(FakeClient)

        def client_cls(*args, **kwargs):
            client = FakeClient(*args, **kwargs)

            async def send_code_request(phone):
                raise _err(terr.FloodWaitError, seconds=7200)

            client.send_code_request = send_code_request
            return client

        mido_auth._import_telethon()["TelegramClient"] = client_cls
        with pytest.raises(mido_auth.LoginError) as excinfo:
            run(
                mido_auth.interactive_login(
                    api_id=1,
                    api_hash="hash",
                    target_stem=tmp_path / "Mido",
                    phone="+201234567890",
                    ask=lambda prompt: "12345",
                    ask_secret=lambda prompt: "unused",
                )
            )
        assert excinfo.value.flood_wait == 7200

    def test_short_flood_wait_is_tolerated(self, fake_telethon, stub_conversion, tmp_path, monkeypatch):
        fake_telethon(FakeClient)

        async def no_sleep(_seconds):
            return None

        monkeypatch.setattr(mido_auth.asyncio, "sleep", no_sleep)

        def client_cls(*args, **kwargs):
            client = FakeClient(*args, **kwargs)
            original = client.send_code_request
            state = {"raised": False}

            async def send_code_request(phone):
                if not state["raised"]:
                    state["raised"] = True
                    raise _err(terr.FloodWaitError, seconds=0)
                return await original(phone)

            client.send_code_request = send_code_request
            return client

        mido_auth._import_telethon()["TelegramClient"] = client_cls
        result = run(
            mido_auth.interactive_login(
                api_id=1,
                api_hash="hash",
                target_stem=tmp_path / "Mido",
                phone="+201234567890",
                ask=lambda prompt: "12345",
                ask_secret=lambda prompt: "unused",
                flood_wait_tolerance=5,
            )
        )
        assert result.ok is True

    def test_cancellation_is_reported(self, fake_telethon, stub_conversion, tmp_path):
        fake_telethon(FakeClient)

        def interrupt(prompt):
            raise KeyboardInterrupt

        with pytest.raises(mido_auth.LoginError) as excinfo:
            run(
                mido_auth.interactive_login(
                    api_id=1,
                    api_hash="hash",
                    target_stem=tmp_path / "Mido",
                    ask=interrupt,
                    ask_secret=lambda prompt: "x",
                )
            )
        assert excinfo.value.kind == "cancelled"

    def test_not_authorized_after_flow_is_an_error(self, fake_telethon, stub_conversion, tmp_path):
        class NeverAuthorizes(FakeClient):
            async def sign_in(self, **kwargs):
                return None

        fake_telethon(NeverAuthorizes)
        with pytest.raises(mido_auth.LoginError) as excinfo:
            run(
                mido_auth.interactive_login(
                    api_id=1,
                    api_hash="hash",
                    target_stem=tmp_path / "Mido",
                    phone="+201234567890",
                    ask=lambda prompt: "12345",
                    ask_secret=lambda prompt: "unused",
                )
            )
        assert "تيليجرام" in str(excinfo.value)


class TestValidation:
    def test_valid_user_session(self, fake_telethon):
        fake_telethon(AuthorizedClient)
        result = run(mido_auth.validate_user_session(api_id=1, api_hash="h", session="data/sessions/Mido"))
        assert result.ok is True
        assert "mido_tester" in (result.identifier or "")
        assert FakeClient.instances[-1].disconnected is True

    def test_unauthorized_session(self, fake_telethon):
        fake_telethon(FakeClient)
        result = run(mido_auth.validate_user_session(api_id=1, api_hash="h", session="path"))
        assert result.ok is False
        assert "غير مصرّح" in result.detail

    def test_revoked_session_has_recovery_hint(self, fake_telethon):
        fake_telethon(RevokedClient)
        result = run(mido_auth.validate_user_session(api_id=1, api_hash="h", session="path"))
        assert result.ok is False
        assert "ملغاة" in result.detail
        assert "repair" in result.detail

    def test_network_error_is_reported(self, fake_telethon):
        fake_telethon(UnreachableClient)
        result = run(mido_auth.validate_user_session(api_id=1, api_hash="h", session="path"))
        assert result.ok is False
        assert "الاتصال" in result.detail

    def test_errors_never_echo_the_api_hash(self, fake_telethon):
        class BadApi(FakeClient):
            async def connect(self):
                raise _err(terr.ApiIdInvalidError)

        fake_telethon(BadApi)
        result = run(mido_auth.validate_user_session(api_id=1, api_hash="SUPER-SECRET-HASH", session="p"))
        assert result.ok is False
        assert "SUPER-SECRET-HASH" not in result.detail

    def test_valid_bot_token(self, fake_telethon):
        fake_telethon(FakeClient)
        result = run(mido_auth.validate_bot_token(api_id=1, api_hash="h", token="123456:AA-valid-token"))
        assert result.ok is True
        assert "mido_tester" in result.detail

    def test_invalid_bot_token(self, fake_telethon):
        fake_telethon(FakeClient)
        result = run(mido_auth.validate_bot_token(api_id=1, api_hash="h", token="123456:AA-wrong"))
        assert result.ok is False
        assert "توكن" in result.detail


class TestStringSessionConversion:
    def test_real_string_session_becomes_a_file_session(self, tmp_path):
        """No mocks here: a genuine Telethon StringSession is converted."""
        import telethon

        if getattr(telethon, "__version__", "0") < "1":  # pragma: no cover
            pytest.skip("telethon missing")
        from telethon.crypto import AuthKey
        from telethon.sessions import SQLiteSession, StringSession

        source = StringSession()
        source.set_dc(2, "149.154.167.51", 443)
        source.auth_key = AuthKey(b"\x02" * 256)
        encoded = source.save()
        assert encoded.startswith("1")

        stem = tmp_path / "Mido"
        written = mido_auth.write_file_session_from_string(encoded, stem)
        path = Path(written)
        assert path == stem.with_name("Mido.session")
        assert path.is_file()

        restored = SQLiteSession(str(stem))
        assert restored.dc_id == 2
        assert restored.server_address == "149.154.167.51"
        assert restored.port == 443
        assert restored.auth_key.key == b"\x02" * 256

    def test_invalid_string_is_rejected(self, tmp_path):
        with pytest.raises(mido_auth.LoginError):
            mido_auth.write_file_session_from_string("1not-a-real-session", tmp_path / "Mido")
