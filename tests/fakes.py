# -*- coding: utf-8 -*-
"""Shared test doubles.

``FakeClient`` implements exactly the Telethon surface ``mido/auth.py`` uses
so the real control flow can be tested without opening a single socket.
"""

from pathlib import Path
from types import SimpleNamespace

import telethon.errors as terr

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


def install_fake_telethon(monkeypatch, client_cls=FakeClient):
    """Point ``mido.auth`` at the fake client, keeping real error classes."""
    from mido import auth as mido_auth

    table = {name: getattr(terr, name) for name in ERROR_NAMES}
    table["TelegramClient"] = client_cls
    table["StringSession"] = lambda value="": ("string", value)
    monkeypatch.setattr(mido_auth, "_import_telethon", lambda: table)
    FakeClient.instances = []
    return table


def write_fake_session_file(string_session, target_stem):
    """Stands in for ``auth.write_file_session_from_string`` (no Telethon)."""
    stem = Path(str(target_stem))
    path = stem.parent / (stem.name + ".session")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"SQLite format 3\x00fake")
    return str(path)
