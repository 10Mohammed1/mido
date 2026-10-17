# -*- coding: utf-8 -*-
"""Mido · Telegram authentication.

All Telethon interaction of the *setup* path lives here:

* validating an existing user session (never trusting the mere existence of a
  ``.session`` file),
* validating a bot token without touching the assistant-bot session file,
* the interactive first login (phone → code → optional two-step password),
* converting a validated ``STRING_SESSION`` into a ``Mido.session`` file.

Nothing in here prints, logs or returns raw secrets: login codes, two-step
passwords and session strings are handled in memory only.  Telethon is
imported lazily so the rest of the package stays import-safe.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Union


class LoginError(RuntimeError):
    """User facing authentication failure (kept free of secrets)."""

    def __init__(self, message: str, *, kind: str = "error", hint: Optional[str] = None, flood_wait: Optional[int] = None):
        super().__init__(message)
        self.kind = kind
        self.hint = hint
        self.flood_wait = flood_wait

    def pretty(self) -> str:
        text = str(self)
        if self.hint:
            text += f"\n   ↳ {self.hint}"
        return text


@dataclass
class ValidationResult:
    ok: bool
    detail: str
    identifier: Optional[str] = None
    error: Optional[str] = None
    flood_wait: Optional[int] = None


@dataclass
class LoginResult:
    ok: bool
    identifier: Optional[str] = None
    session_file: Optional[str] = None
    string_session: Optional[str] = field(default=None, repr=False)  # never repr()ed
    me: Optional[object] = field(default=None, repr=False)


# ── helpers ──────────────────────────────────────────────────────────────────
def _import_telethon():
    from telethon import TelegramClient  # noqa: WPS433 (lazy import on purpose)
    from telethon.errors import (  # noqa: WPS433
        AccessTokenExpiredError,
        AccessTokenInvalidError,
        ApiIdInvalidError,
        AuthKeyDuplicatedError,
        AuthKeyUnregisteredError,
        FloodWaitError,
        PasswordHashInvalidError,
        PhoneCodeExpiredError,
        PhoneCodeInvalidError,
        PhoneNumberBannedError,
        PhoneNumberInvalidError,
        SessionPasswordNeededError,
        SessionRevokedError,
        UserDeactivatedBanError,
        UserDeactivatedError,
    )
    from telethon.sessions import StringSession  # noqa: WPS433

    return {
        "TelegramClient": TelegramClient,
        "StringSession": StringSession,
        "AccessTokenExpiredError": AccessTokenExpiredError,
        "AccessTokenInvalidError": AccessTokenInvalidError,
        "ApiIdInvalidError": ApiIdInvalidError,
        "AuthKeyDuplicatedError": AuthKeyDuplicatedError,
        "AuthKeyUnregisteredError": AuthKeyUnregisteredError,
        "FloodWaitError": FloodWaitError,
        "PasswordHashInvalidError": PasswordHashInvalidError,
        "PhoneCodeExpiredError": PhoneCodeExpiredError,
        "PhoneCodeInvalidError": PhoneCodeInvalidError,
        "PhoneNumberBannedError": PhoneNumberBannedError,
        "PhoneNumberInvalidError": PhoneNumberInvalidError,
        "SessionPasswordNeededError": SessionPasswordNeededError,
        "SessionRevokedError": SessionRevokedError,
        "UserDeactivatedBanError": UserDeactivatedBanError,
        "UserDeactivatedError": UserDeactivatedError,
    }


def _describe_account(me) -> str:
    if me is None:
        return "(غير معروف)"
    parts = [getattr(me, "first_name", None) or "", getattr(me, "last_name", None) or ""]
    name = " ".join(part for part in parts if part).strip() or "(بدون اسم)"
    username = getattr(me, "username", None)
    return f"{name} (@{username})" if username else name


def _friendly_exception(exc: Exception, errors: dict) -> LoginError:
    """Translate Telethon errors into actionable, secret-free messages."""
    if isinstance(exc, errors["PhoneNumberInvalidError"]):
        return LoginError(
            "رقم الهاتف غير صحيح.",
            hint="اكتب الرقم بصيغة دولية كاملة مثل +201234567890.",
        )
    if isinstance(exc, errors["PhoneNumberBannedError"]):
        return LoginError("رقم الهاتف محظور من تيليجرام.", hint="استخدم رقمًا آخر أو راجع تيليجرام.")
    if isinstance(exc, errors["PhoneCodeInvalidError"]):
        return LoginError("كود الدخول غير صحيح.", hint="تأكد من الكود كما وصل في تيليجرام (بدون مسافات).")
    if isinstance(exc, errors["PhoneCodeExpiredError"]):
        return LoginError("انتهت صلاحية كود الدخول.", hint="اطلب كودًا جديدًا ثم أدخله فورًا.")
    if isinstance(exc, errors["PasswordHashInvalidError"]):
        return LoginError("كلمة مرور التحقق بخطوتين غير صحيحة.", hint="أعد المحاولة أو راجع كلمة المرور من إعدادات تيليجرام.")
    if isinstance(exc, errors["FloodWaitError"]):
        seconds = int(getattr(exc, "seconds", 0) or 0)
        return LoginError(
            "تيليجرام طلب الانتظار قبل إعادة المحاولة.",
            kind="flood",
            hint=f"انتظر {seconds} ثانية ثم أعد المحاولة.",
            flood_wait=seconds,
        )
    if isinstance(exc, errors["ApiIdInvalidError"]):
        return LoginError(
            "API_ID / API_HASH غير صحيحين.",
            hint="احصل عليهما من my.telegram.org ثم اكتبهما في .env أو شغّل mido_setup.py setup من جديد.",
        )
    if isinstance(exc, errors["AuthKeyUnregisteredError"]) or isinstance(exc, errors["SessionRevokedError"]):
        return LoginError(
            "الجلسة ملغاة أو منتهية.",
            hint="الجلسة أُلغيت من تيليجرام. شغّل mido_setup.py repair لتسجيل دخول جديد (لن تُحذف الجلسة القديمة).",
        )
    if isinstance(exc, errors["AuthKeyDuplicatedError"]):
        return LoginError(
            "تم استخدام نفس الجلسة من جهازين ضد قوانين تيليجرام.",
            hint="أغلق الجهاز الآخر ثم شغّل mido_setup.py repair لتسجيل دخول جديد.",
        )
    if isinstance(exc, errors["UserDeactivatedBanError"]) or isinstance(exc, errors["UserDeactivatedError"]):
        return LoginError("الحساب محظور أو موقوف من تيليجرام.", hint="راجع حالة الحساب مع تيليجرام.")
    if isinstance(exc, (ConnectionError, TimeoutError, OSError, asyncio.TimeoutError)):
        return LoginError(
            "خطأ في الاتصال بتيليجرام (شبكة / بروكسي).",
            hint="تأكد من الإنترنت، أو أن البروكسي مسموح في إعدادات الشبكة على السيرفر.",
        )
    return LoginError(f"فشل غير متوقع: {type(exc).__name__}: {exc}")


async def validate_user_session(*, api_id: int, api_hash: str, session: Union[str, object]) -> ValidationResult:
    """Connect with *session* and ask Telegram whether the account is valid."""
    tt = _import_telethon()
    client = tt["TelegramClient"](session, api_id, api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return ValidationResult(
                ok=False,
                detail="الجلسة موجودة لكن غير مصرّح لها (تحتاج تسجيل دخول جديد).",
                error="Unauthorized",
            )
        me = await client.get_me()
        if me is None:
            return ValidationResult(ok=False, detail="تعذّر التحقق من الحساب.", error="NoAccount")
        return ValidationResult(ok=True, detail=f"الجلسة صالحة ✓ ({type(session).__name__ if not isinstance(session, str) else 'file'})", identifier=_describe_account(me))
    except Exception as exc:  # noqa: BLE001 - translated to a user facing error
        friendly = _friendly_exception(exc, tt)
        return ValidationResult(ok=False, detail=friendly.pretty(), error=type(exc).__name__, flood_wait=friendly.flood_wait)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def validate_bot_token(*, api_id: int, api_hash: str, token: str) -> ValidationResult:
    """Verify a BotFather token without creating a session file."""
    tt = _import_telethon()
    client = tt["TelegramClient"](tt["StringSession"](), api_id, api_hash)
    try:
        await client.start(bot_token=token)
        me = await client.get_me()
        if me is None:
            return ValidationResult(ok=False, detail="تم الاتصال لكن تعذّر قراءة بيانات البوت.", error="NoBot")
        return ValidationResult(ok=True, detail=f"توكن البوت صالح ✓ (@{me.username})", identifier=f"@{me.username}" if me.username else _describe_account(me))
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, (tt["AccessTokenInvalidError"], tt["AccessTokenExpiredError"])):
            return ValidationResult(
                ok=False,
                detail="توكن البوت غير صحيح أو منتهي.",
                error=type(exc).__name__,
            )
        friendly = _friendly_exception(exc, tt)
        return ValidationResult(ok=False, detail=friendly.pretty(), error=type(exc).__name__, flood_wait=friendly.flood_wait)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


def write_file_session_from_string(string_session: str, target_stem: Union[str, Path]) -> str:
    """Persist a validated ``STRING_SESSION`` as an on-disk Telethon session."""
    from telethon.crypto import AuthKey  # noqa: WPS433
    from telethon.sessions import SQLiteSession, StringSession  # noqa: WPS433

    try:
        source = StringSession(string_session)
        auth_key = source.auth_key
        dc_id, address, port = source.dc_id, source.server_address, source.port
    except Exception as exc:  # malformed / truncated / copied-with-spaces
        raise LoginError(
            "كود الجلسة النصية غير صالح أو ناقص.",
            kind="string",
            hint="تأكد أنك نسخت كود STRING_SESSION كاملًا ومن مصدر موثوق.",
        ) from exc
    if not auth_key or not dc_id:
        raise LoginError("كود الجلسة النصية لا يحتوي على مفتاح صالح.", kind="string")
    stem = Path(str(target_stem))
    stem.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination = SQLiteSession(str(stem))
        destination.set_dc(dc_id, address, port)
        destination.auth_key = AuthKey(data=bytes(auth_key.key))
        destination.save()
    except Exception as exc:  # disk full / permissions / corrupt target
        raise LoginError(f"تعذّر حفظ ملف الجلسة: {type(exc).__name__}: {exc}") from exc
    return destination.filename


async def interactive_login(
    *,
    api_id: int,
    api_hash: str,
    target_stem: Union[str, Path],
    phone: Optional[str] = None,
    ask: Optional[Callable[[str], str]] = None,
    ask_secret: Optional[Callable[[str], str]] = None,
    notify: Optional[Callable[[str], None]] = None,
    max_code_attempts: int = 3,
    max_password_attempts: int = 3,
    flood_wait_tolerance: int = 60,
) -> LoginResult:
    """Full first-time login: phone → code → (two-step password if asked)."""
    import getpass

    ask = ask or (lambda prompt: input(prompt))
    ask_secret = ask_secret or (lambda prompt: getpass.getpass(prompt))
    notify = notify or (lambda message: print(message))
    tt = _import_telethon()
    errors = tt
    client = tt["TelegramClient"](tt["StringSession"](), api_id, api_hash)

    async def _flood(exc) -> None:
        seconds = int(getattr(exc, "seconds", 0) or 0)
        if seconds <= flood_wait_tolerance:
            notify(f"⏳ تيليجرام طلب الانتظار {seconds} ثانية قبل إعادة المحاولة…")
            await asyncio.sleep(seconds + 1)
            return
        raise _friendly_exception(exc, errors) from exc

    try:
        await client.connect()
        if await client.is_user_authorized():
            me = await client.get_me()
            notify("ℹ️ الجلسة المؤقتة مصرّح لها بالفعل — سيتم حفظها.")
        else:
            phone = (phone or ask("📱 اكتب رقم الهاتف بصيغة دولية (مثال +201234567890): ")).strip()
            phone = phone.replace(" ", "")
            sent = None
            attempts = 0
            while attempts < max_code_attempts:
                attempts += 1
                try:
                    if sent is None:
                        sent = await client.send_code_request(phone)
                        notify("📨 تم إرسال كود الدخول إلى تيليجرام (رسالة داخل التطبيق أو SMS).")
                    code = ask("🔢 اكتب كود الدخول: ").strip()
                    await client.sign_in(phone=phone, code=code, phone_code_hash=sent.phone_code_hash)
                    break
                except errors["SessionPasswordNeededError"]:
                    notify("🔐 الحساب محمي بالتحقق بخطوتين (Two-Step).")
                    for password_attempt in range(1, max_password_attempts + 1):
                        password = ask_secret("🔑 اكتب كلمة مرور التحقق بخطوتين (لن تظهر): ")
                        try:
                            await client.sign_in(password=password)
                            break
                        except errors["PasswordHashInvalidError"]:
                            notify(f"❌ كلمة المرور غير صحيحة ({password_attempt}/{max_password_attempts}).")
                            if password_attempt == max_password_attempts:
                                raise
                        except errors["FloodWaitError"] as exc:
                            await _flood(exc)
                    break
                except errors["PhoneCodeInvalidError"] as exc:
                    # a wrong code can simply be re-entered
                    notify(f"❌ {_friendly_exception(exc, errors)}")
                    if attempts >= max_code_attempts:
                        raise
                    notify("🔁 جرّب إدخال الكود مرة أخرى…")
                except errors["PhoneCodeExpiredError"] as exc:
                    # an expired code needs a brand new one
                    notify(f"❌ {_friendly_exception(exc, errors)}")
                    if attempts >= max_code_attempts:
                        raise
                    sent = None
                    notify("📨 سيتم إرسال كود جديد…")
                except errors["FloodWaitError"] as exc:
                    await _flood(exc)

        if not await client.is_user_authorized():
            raise LoginError("لم يتم تأكيد الجلسة من تيليجرام.", hint="أعد المحاولة أو راجع الأخطاء السابقة.")
        me = await client.get_me()
        string_session = client.session.save()
        if not string_session:
            raise LoginError("تعذّر استخراج بيانات الجلسة من تيليجرام.")
        session_file = write_file_session_from_string(string_session, target_stem)
        return LoginResult(ok=True, identifier=_describe_account(me), session_file=session_file, string_session=string_session, me=me)
    except LoginError:
        raise
    except KeyboardInterrupt as exc:
        raise LoginError("تم إلغاء تسجيل الدخول.", kind="cancelled") from exc
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, errors["FloodWaitError"]):
            raise _friendly_exception(exc, errors) from exc
        raise _friendly_exception(exc, errors) from exc
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


def run_async(coro, *, timeout: Optional[float] = None):
    """Run a coroutine on a *fresh* loop (setup never touches the bot loop)."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        if timeout is not None:
            return loop.run_until_complete(asyncio.wait_for(coro, timeout))
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.close()
        finally:
            asyncio.set_event_loop(None)
