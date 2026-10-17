# -*- coding: utf-8 -*-
"""Mido · setup & diagnostics CLI.

Commands (identical whether called as ``python mido_setup.py <cmd>`` or
``python -m zira <cmd>``):

``check``
    Head-less self test: configuration, secrets presence (masked),
    dependencies, session inventory / lock state and — with ``--online`` —
    the real authorization state against Telegram.
``setup``
    First-time setup: reuse a valid session, import an existing ``.session``
    file, migrate a ``STRING_SESSION``, or run the interactive phone → code →
    two-step login.  Validates the bot token and writes ``.env`` (backed up,
    locked down).
``import-session PATH``
    Validate and copy an existing Telethon session into ``data/sessions/``.
``sessions``
    Inventory of the session files found (metadata only).
``repair``
    Guided re-authentication for a revoked/corrupt session.  Never deletes a
    session: the old file is preserved as a ``.bak-<timestamp>`` copy.

Secrets are never echoed, logged or passed as command-line arguments; the
installer supplies optional values through ``MIDO_SETUP_*`` environment
variables.
"""

from __future__ import annotations

import argparse
import getpass
import importlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mido import auth as mido_auth  # noqa: E402
from mido import config_io  # noqa: E402
from mido import session as mido_session  # noqa: E402

CORE_IMPORTS = (
    "telethon",
    "dotenv",
    "sqlalchemy",
    "aiohttp",
    "PIL",
    "psutil",
    "pytz",
    "requests",
    "motor",
    "emoji",
    "yt_dlp",
)

ICON_OK = "✓"
ICON_BAD = "✗"
ICON_INFO = "•"


def out(message: str = "") -> None:
    print(message)


def section(title: str) -> None:
    out("")
    out(f"── {title} " + "─" * max(0, 60 - len(title)))


# ── configuration helpers ────────────────────────────────────────────────────
def load_effective_config() -> Dict[str, object]:
    """Mirror the bot's own configuration loading order (safe, no network).

    The ``.env`` file is read without touching ``os.environ`` and its values
    win over the defaults of the configuration module — exactly the rule the
    bot applies at import time.
    """
    values: Dict[str, object] = {}
    env_file = config_io.read_env_file()
    for key, value in env_file.items():
        values[key] = value
    values["_env_file"] = env_file
    module = None
    try:
        if os.environ.get("ENV"):
            module = importlib.import_module("sample_config")
            values.setdefault("config_module", "sample_config.py (ENV mode)")
        elif (Path.cwd() / "config.py").is_file():
            module = importlib.import_module("config")
            values.setdefault("config_module", "config.py")
        else:
            module = importlib.import_module("sample_config")
            values.setdefault("config_module", "sample_config.py")
    except Exception as exc:  # noqa: BLE001
        values["config_error"] = str(exc)
        module = None
    if module is not None:
        cls = getattr(module, "Development", None) or getattr(module, "Config", None)
        if cls is not None:
            for key in (
                "APP_ID",
                "API_HASH",
                "TG_BOT_TOKEN",
                "TG_BOT_USERNAME",
                "OWNER_ID",
                "ALIVE_NAME",
                "DB_URI",
                "STRING_SESSION",
                "SESSION_DIR",
                "SESSION_NAME",
                "BOT_SESSION_NAME",
                "SESSION_SOURCE",
                "NO_LOAD",
                "COMMAND_HAND_LER",
            ):
                values.setdefault(key, getattr(cls, key, None))
    # make the session settings visible to `mido.session` helpers without
    # overriding anything the real environment already defines
    for key in (
        "SESSION_DIR",
        "SESSION_NAME",
        "BOT_SESSION_NAME",
        "SESSION_SOURCE",
    ):
        if values.get(key):
            os.environ.setdefault(key, str(values[key]))
    return values


def _cred(name: str, value, *, secret: bool = False) -> str:
    if value in (None, "", 0):
        return f"{ICON_BAD} {name}: غير مضبوط"
    if secret:
        return f"{ICON_OK} {name}: {config_io.mask(str(value))}"
    return f"{ICON_OK} {name}: {value}"


def user_location(config: Optional[Dict[str, object]] = None) -> mido_session.SessionLocation:
    config = config or {}
    return mido_session.locate_session(
        str(config.get("SESSION_NAME") or mido_session.session_name("user")),
        directory=mido_session.resolve_session_dir(str(config.get("SESSION_DIR")) if config.get("SESSION_DIR") else None),
    )


def bot_location(config: Optional[Dict[str, object]] = None) -> mido_session.SessionLocation:
    config = config or {}
    return mido_session.locate_session(
        str(config.get("BOT_SESSION_NAME") or mido_session.session_name("bot")),
        directory=mido_session.resolve_session_dir(str(config.get("SESSION_DIR")) if config.get("SESSION_DIR") else None),
    )


# ── check ────────────────────────────────────────────────────────────────────
def cmd_check(args) -> int:
    config = load_effective_config()
    report: Dict[str, object] = {"ok": True, "problems": [], "warnings": []}
    online = bool(getattr(args, "online", False))

    section("البيئة")
    out(f"{ICON_INFO} النظام: {platform.system()} {platform.release()} ({platform.machine()})")
    out(f"{ICON_INFO} بايثون: {platform.python_version()} ({sys.executable})")
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    out(f"{ICON_INFO} بيئة معزولة (venv): {'نعم' if in_venv else 'لأ — يُفضّل تشغيل البوت داخل venv'}")
    out(f"{ICON_INFO} مجلد المشروع: {mido_session.project_root()}")
    report["python"] = platform.python_version()
    report["in_venv"] = in_venv
    if not in_venv:
        report["warnings"].append("not_in_venv")

    section("الإعدادات")
    env_file = mido_session.project_root() / ".env"
    out(f"{ICON_INFO} ملف .env: {'موجود' if env_file.is_file() else 'غير موجود'}")
    if config_io.config_py_present():
        out(f"{ICON_INFO} config.py: موجود (يُستخدم كإعداد محلي)")
    out(_cred("APP_ID", config.get("APP_ID")))
    out(_cred("API_HASH", config.get("API_HASH"), secret=True))
    out(_cred("TG_BOT_TOKEN", config.get("TG_BOT_TOKEN"), secret=True))
    out(_cred("STRING_SESSION", config.get("STRING_SESSION"), secret=True))
    if not config.get("APP_ID"):
        report["problems"].append("APP_ID غير مضبوط")
    if not config.get("API_HASH"):
        report["problems"].append("API_HASH غير مضبوط")
    if not config.get("TG_BOT_TOKEN"):
        report["problems"].append("TG_BOT_TOKEN غير مضبوط (مطلوب لعميل البوت المساعد)")

    section("الحزم")
    missing: List[str] = []
    for name in CORE_IMPORTS:
        try:
            importlib.import_module(name)
            out(f"{ICON_OK} {name}")
        except Exception as exc:  # noqa: BLE001
            missing.append(name)
            out(f"{ICON_BAD} {name}: {exc}")
    if missing:
        report["problems"].append("حزم ناقصة: " + ", ".join(missing))
    report["missing_packages"] = missing

    section("الجلسات")
    user_loc = user_location(config)
    bot_loc = bot_location(config)
    out(f"{ICON_INFO} مجلد الجلسات: {mido_session.resolve_session_dir(str(config.get('SESSION_DIR')) if config.get('SESSION_DIR') else None)}")
    out(f"{ICON_INFO} جلسة المستخدم: {user_loc.describe()}")
    out(f"{ICON_INFO} جلسة البوت: {bot_loc.describe()}")
    lock = mido_session.session_lock_status(user_loc)
    if lock["running"]:
        out(f"{ICON_INFO} نسخة أخرى تعمل الآن على نفس الجلسة (pid {lock['pid']})")
        report["warnings"].append("instance_running")
    elif lock["stale"]:
        out(f"{ICON_INFO} قفل قديم (عملية منتهية) — سيُستبدل تلقائيًا عند التشغيل")
    if user_loc.exists:
        valid, message = mido_session.validate_session_file(user_loc.file)
        out(f"{ICON_OK if valid else ICON_BAD} فحص ملف جلسة المستخدم: {'سليم' if valid else message}")
        if not valid:
            report["problems"].append("ملف جلسة المستخدم تالف")
    else:
        string_present = bool(config.get("STRING_SESSION"))
        source = mido_session.session_source(
            str(config.get("STRING_SESSION") or ""),
            prefer=str(config.get("SESSION_SOURCE") or "auto"),
            file_exists=False,
        )
        if string_present and source == "string":
            out(f"{ICON_OK} لا يوجد ملف جلسة — سيتم استخدام STRING_SESSION")
        else:
            out(f"{ICON_BAD} لا يوجد أي مصدر لجلسة المستخدم (ملف أو STRING_SESSION)")
            report["problems"].append("لا توجد جلسة مستخدم — شغّل mido_setup.py setup")
    report["user_session"] = user_loc.describe()
    report["bot_session"] = bot_loc.describe()

    section("الملحقات")
    plugins_dir = mido_session.project_root() / "zira" / "plugins"
    plugin_count = len(list(plugins_dir.glob("*.py"))) if plugins_dir.is_dir() else 0
    out(f"{ICON_INFO} عدد ملفات الملحقات: {plugin_count}")
    if plugin_count == 0:
        report["problems"].append("مجلد الملحقات فارغ أو غير موجود")
    report["plugins"] = plugin_count

    if online:
        section("فحص أونلاين (يتصل بتيليجرام)")
        api_id, api_hash = config.get("APP_ID"), config.get("API_HASH")
        if api_id and api_hash:
            source = mido_session.session_source(
                str(config.get("STRING_SESSION") or ""),
                prefer=str(config.get("SESSION_SOURCE") or "auto"),
                file_exists=user_loc.exists,
            )
            target = str(user_loc.stem) if source == "file" else mido_auth._import_telethon()["StringSession"](str(config.get("STRING_SESSION") or ""))
            result = mido_auth.run_async(
                mido_auth.validate_user_session(api_id=int(api_id), api_hash=str(api_hash), session=target), timeout=90
            )
            out(f"{ICON_OK if result.ok else ICON_BAD} جلسة المستخدم: {result.detail}")
            report["user_online"] = result.ok
            if not result.ok:
                report["problems"].append("جلسة المستخدم غير صالحة (أونلاين)")
            if config.get("TG_BOT_TOKEN"):
                bot_result = mido_auth.run_async(
                    mido_auth.validate_bot_token(api_id=int(api_id), api_hash=str(api_hash), token=str(config.get("TG_BOT_TOKEN"))),
                    timeout=90,
                )
                out(f"{ICON_OK if bot_result.ok else ICON_BAD} توكن البوت: {bot_result.detail}")
                report["bot_online"] = bot_result.ok
                if not bot_result.ok:
                    report["problems"].append("توكن البوت غير صالح (أونلاين)")
        else:
            out(f"{ICON_BAD} لا يمكن الفحص أونلاين بدون APP_ID/API_HASH")

    report["ok"] = not report["problems"]
    section("النتيجة")
    if report["ok"]:
        out(f"{ICON_OK} كل الفحوصات الأساسية ناجحة.")
    else:
        out(f"{ICON_BAD} توجد مشاكل:")
        for problem in report["problems"]:
            out(f"   - {problem}")
    for warning in report["warnings"]:
        out(f"   ⚠ {warning}")

    if getattr(args, "json", False):
        out(json.dumps(report, ensure_ascii=False))
    return 0 if report["ok"] else 1


# ── setup ────────────────────────────────────────────────────────────────────
def _env_or(default: Optional[str], key: str) -> Optional[str]:
    return os.environ.get(key) or default


def cmd_setup(args) -> int:
    config = load_effective_config()
    interactive = not bool(getattr(args, "non_interactive", False)) and not os.environ.get("MIDO_SETUP_NON_INTERACTIVE")
    api_id = getattr(args, "api_id", None) or _env_or(None, "MIDO_SETUP_APP_ID") or config.get("APP_ID")
    api_hash = getattr(args, "api_hash", None) or _env_or(None, "MIDO_SETUP_API_HASH") or config.get("API_HASH")
    bot_token = _env_or(None, "MIDO_SETUP_BOT_TOKEN") or config.get("TG_BOT_TOKEN")
    alive_name = _env_or(None, "MIDO_SETUP_ALIVE_NAME") or config.get("ALIVE_NAME")
    owner_id = _env_or(None, "MIDO_SETUP_OWNER_ID") or config.get("OWNER_ID")
    import_file = getattr(args, "import_session", None) or _env_or(None, "MIDO_SETUP_SESSION_FILE")
    force_login = bool(getattr(args, "force_login", False)) or os.environ.get("MIDO_SETUP_FORCE_LOGIN") == "1"

    def ask(prompt: str) -> str:
        return input(prompt)

    def ask_secret(prompt: str) -> str:
        return getpass.getpass(prompt)

    section("Mido setup — الإعداد الأولي")
    if config.get("config_module") == "config.py":
        out(f"{ICON_INFO} ملاحظة: يوجد config.py محلي — القيم التي تختارها هنا ستُكتب في .env وستكون لها الأولوية.")

    # 1) API credentials -----------------------------------------------------
    if not api_id:
        if not interactive:
            out(f"{ICON_BAD} APP_ID مطلوب (مرّره عبر MIDO_SETUP_APP_ID)")
            return 1
        out("")
        out("احصل على APP_ID و API_HASH من https://my.telegram.org → API development tools")
        api_id = ask("🔑 APP_ID: ").strip()
    if not api_hash:
        if not interactive:
            out(f"{ICON_BAD} API_HASH مطلوب (مرّره عبر MIDO_SETUP_API_HASH)")
            return 1
        api_hash = ask_secret("🔑 API_HASH (لن يظهر): ").strip()
    try:
        api_id_int = int(str(api_id).strip())
    except (TypeError, ValueError):
        out(f"{ICON_BAD} APP_ID يجب أن يكون رقمًا صحيحًا.")
        return 1
    if not api_hash:
        out(f"{ICON_BAD} API_HASH فارغ.")
        return 1
    out(f"{ICON_OK} APP_ID / API_HASH تم استلامهما ({config_io.mask(str(api_hash))}).")

    # 2) user session --------------------------------------------------------
    user_loc = user_location(config)
    out("")
    out(f"{ICON_INFO} مسار جلسة المستخدم: {user_loc.file}")
    session_updates: Dict[str, str] = {}

    need_login = False
    if force_login:
        need_login = True
    elif user_loc.exists:
        ok, message = mido_session.validate_session_file(user_loc.file)
        if not ok:
            out(f"{ICON_BAD} ملف الجلسة الحالي غير صالح: {message}")
            out(f"{ICON_INFO} سيتم تسجيل دخول جديد. الجلسة القديمة ستُحفظ كنسخة .bak ولن تُحذف.")
            need_login = True
        else:
            out("⌛ يتم التحقق من الجلسة الحالية مع تيليجرام…")
            result = mido_auth.run_async(
                mido_auth.validate_user_session(api_id=api_id_int, api_hash=api_hash, session=str(user_loc.stem)),
                timeout=120,
            )
            if result.ok:
                out(f"{ICON_OK} جلسة صالحة — سيتم استخدامها مباشرة ({result.identifier})")
            else:
                out(f"{ICON_INFO} {result.detail}")
                if not interactive:
                    out(f"{ICON_BAD} الجلسة الحالية غير صالحة والوضع غير تفاعلي — لا يمكن المتابعة.")
                    return 1
                out("ℹ️ ستحتاج تسجيل دخول جديد (خطوة لمرة واحدة فقط).")
                need_login = True
    else:
        need_login = True

    if need_login:
        import_from = import_file
        if import_from is None and interactive and not force_login:
            candidate = ask("📥 لو عندك ملف .session جاهز اكتب مساره (أو اتركه فارغًا لتسجيل دخول جديد): ").strip().strip('"')
            import_from = candidate or None
        imported = False
        if import_from:
            out(f"⌛ يتم التحقق من الملف المستورد: {import_from}")
            try:
                location, backup = mido_session.import_session_file(
                    import_from, name=user_loc.name, directory=user_loc.stem.parent, force=bool(getattr(args, "force", False))
                )
            except mido_session.SessionImportError as exc:
                out(f"{ICON_BAD} {exc}")
                return 1
            if backup:
                out(f"{ICON_INFO} تم حفظ الجلسة السابقة في: {backup}")
            result = mido_auth.run_async(
                mido_auth.validate_user_session(api_id=api_id_int, api_hash=api_hash, session=str(location.stem)), timeout=120
            )
            if result.ok:
                out(f"{ICON_OK} تم استيراد الجلسة والتحقق منها بنجاح ({result.identifier})")
                user_loc = location
                imported = True
            else:
                out(f"{ICON_BAD} الملف المستورد غير صالح: {result.detail}")
                return 1

        string_value = str(getattr(args, "string_session", None) or config.get("STRING_SESSION") or "")
        if not imported and string_value and interactive and not force_login:
            migrate = ask("🔁 يوجد STRING_SESSION — أحفظه كملف جلسة (بدون تسجيل دخول جديد)؟ (Y/n): ").strip().lower()
            if migrate in ("", "y", "yes", "نعم"):
                existed_before_migration = user_loc.exists
                try:
                    session_file = mido_auth.write_file_session_from_string(string_value, user_loc.stem)
                except mido_auth.LoginError as exc:
                    out(f"{ICON_BAD} تعذّر تحويل الكود إلى ملف جلسة: {exc}")
                else:
                    result = mido_auth.run_async(
                        mido_auth.validate_user_session(api_id=api_id_int, api_hash=api_hash, session=str(user_loc.stem)),
                        timeout=120,
                    )
                    if result.ok:
                        out(f"{ICON_OK} تم حفظ الكود كملف جلسة والتحقق منه ({result.identifier}): {session_file}")
                        imported = True
                    else:
                        out(f"{ICON_BAD} فشل التحقق من الملف الناتج: {result.detail}")
                        if not existed_before_migration:
                            removed = mido_session.cleanup_partial_session(user_loc)
                            for path in removed:
                                out(f"{ICON_INFO} تم حذف ملف غير صالح ناتج عن المحاولة: {path}")

        if not imported:
            if not interactive:
                out(f"{ICON_BAD} لا توجد جلسة صالحة ولا يمكن تسجيل دخول غير تفاعلي.")
                return 1
            existed_before = user_loc.exists
            if existed_before:
                backup = mido_session.backup_session(user_loc)
                out(f"{ICON_INFO} تم الاحتفاظ بنسخة من الجلسة القديمة في: {backup}")
            out("")
            out("📱 تسجيل دخول جديد — سيُطلب رقم الهاتف ثم الكود (ثم كلمة مرور التحقق بخطوتين إن كانت مفعّلة).")
            out("   (لا يحتاج أي أحد غيرك لهذه البيانات، ولا تُرسل لأي جهة أخرى)")
            try:
                login = mido_auth.run_async(
                    mido_auth.interactive_login(
                        api_id=api_id_int,
                        api_hash=api_hash,
                        target_stem=user_loc.stem,
                        phone=_env_or(None, "MIDO_SETUP_PHONE"),
                        ask=ask,
                        ask_secret=ask_secret,
                    )
                )
            except mido_auth.LoginError as exc:
                if not existed_before:
                    for path in mido_session.cleanup_partial_session(user_loc):
                        out(f"{ICON_INFO} تم تنظيف ملف مؤقت: {path}")
                out(f"{ICON_BAD} فشل تسجيل الدخول: {exc.pretty()}")
                return 1
            out(f"{ICON_OK} تم تسجيل الدخول بنجاح: {login.identifier}")
            out(f"{ICON_OK} تم حفظ الجلسة في: {login.session_file}")
            if getattr(args, "save_string", False) and login.string_session:
                session_updates["STRING_SESSION"] = login.string_session
                out(f"{ICON_INFO} تم حفظ نسخة STRING_SESSION أيضًا (يمكن استخدامها على سيرفر آخر).")

    # 3) bot token -----------------------------------------------------------
    if not bot_token:
        if not interactive:
            out(f"{ICON_BAD} TG_BOT_TOKEN مطلوب (مرّره عبر MIDO_SETUP_BOT_TOKEN)")
            return 1
        out("")
        out("توكن البوت: من @BotFather → /newbot أو /mybots → API Token")
        bot_token = ask_secret("🤖 توكن البوت (لن يظهر): ").strip()
    if bot_token:
        out("⌛ يتم التحقق من توكن البوت…")
        bot_result = mido_auth.run_async(
            mido_auth.validate_bot_token(api_id=api_id_int, api_hash=api_hash, token=str(bot_token)), timeout=120
        )
        if not bot_result.ok:
            out(f"{ICON_BAD} توكن البوت غير صالح: {bot_result.detail}")
            return 1
        out(f"{ICON_OK} {bot_result.detail}")

    # 4) persist -------------------------------------------------------------
    updates: Dict[str, str] = {
        "APP_ID": str(api_id_int),
        "API_HASH": str(api_hash),
        "TG_BOT_TOKEN": str(bot_token),
        "SESSION_DIR": str(mido_session.DEFAULT_SESSION_DIR),
        "SESSION_NAME": user_loc.name,
        "BOT_SESSION_NAME": mido_session.session_name("bot"),
    }
    if alive_name:
        updates["ALIVE_NAME"] = str(alive_name)
    if owner_id:
        updates["OWNER_ID"] = str(owner_id)
    if getattr(args, "string_session", None):
        updates["STRING_SESSION"] = str(args.string_session)
    updates.update(session_updates)
    path, backup = config_io.write_env_file(updates)
    out("")
    out(f"{ICON_OK} تم حفظ الإعدادات في: {path}")
    if backup:
        out(f"{ICON_INFO} نسخة احتياطية للإعدادات السابقة: {backup}")
    out(f"{ICON_INFO} الصلاحيات: {config_io.harden_file(path)}")

    section("الخطوات التالية")
    out(f"{ICON_INFO} لتشغيل البوت:  python -m zira")
    out(f"{ICON_INFO} لفحص شامل:    python mido_setup.py check --online")
    out(f"{ICON_INFO} ملفات حساسة لا تشاركها: .env / data/sessions/*.session / *.db")
    return 0


# ── import-session ───────────────────────────────────────────────────────────
def cmd_import_session(args) -> int:
    config = load_effective_config()
    target_name = getattr(args, "name", None) or str(config.get("SESSION_NAME") or mido_session.session_name("user"))
    directory = mido_session.resolve_session_dir(str(config.get("SESSION_DIR")) if config.get("SESSION_DIR") else None)
    try:
        location, backup = mido_session.import_session_file(
            args.path, name=target_name, directory=directory, force=bool(getattr(args, "force", False))
        )
    except mido_session.SessionImportError as exc:
        out(f"{ICON_BAD} {exc}")
        return 1
    if backup:
        out(f"{ICON_INFO} تم حفظ الجلسة السابقة في: {backup}")
    out(f"{ICON_OK} تم استيراد الجلسة إلى: {location.file}")

    api_id, api_hash = config.get("APP_ID"), config.get("API_HASH")
    if api_id and api_hash and not getattr(args, "no_verify", False):
        result = mido_auth.run_async(
            mido_auth.validate_user_session(api_id=int(api_id), api_hash=str(api_hash), session=str(location.stem)), timeout=120
        )
        out(f"{ICON_OK if result.ok else ICON_BAD} تحقق تيليجرام: {result.detail}")
        if not result.ok:
            return 1
    else:
        out(f"{ICON_INFO} تم تخطي التحقق أونلاين (لا توجد مفاتيح APP_ID/API_HASH أو طُلب --no-verify).")
    return 0


# ── sessions ─────────────────────────────────────────────────────────────────
def cmd_sessions(args) -> int:
    config = load_effective_config()
    directory = mido_session.resolve_session_dir(str(config.get("SESSION_DIR")) if config.get("SESSION_DIR") else None)
    section("الجلسات المكتشفة")
    entries = mido_session.list_session_files(directory)
    if not entries:
        out("لا توجد ملفات جلسات على هذا الجهاز.")
    for entry in entries:
        state = ICON_OK if entry["valid"] else ICON_BAD
        out(f"{state} {entry['file']}")
        out(f"    الحجم: {entry['size']} بايت — آخر تعديل: {entry['modified']}")
        lock = entry.get("lock") or {}
        if lock.get("running"):
            out(f"    ⚠ مستخدمة الآن من عملية pid {lock.get('pid')}")
    section("المصدر المستخدم حاليًا")
    user_loc = user_location(config)
    source = mido_session.session_source(
        str(config.get("STRING_SESSION") or ""),
        prefer=str(config.get("SESSION_SOURCE") or "auto"),
        file_exists=user_loc.exists,
    )
    out(f"{ICON_INFO} SESSION_SOURCE={config.get('SESSION_SOURCE') or 'auto'} → المصدر الفعلي: {source}")
    if source == "string":
        out(f"{ICON_INFO} STRING_SESSION: {config_io.mask(str(config.get('STRING_SESSION') or ''))}")
    else:
        out(f"{ICON_INFO} ملف الجلسة: {user_loc.file}")
    if getattr(args, "json", False):
        out(json.dumps({"sessions": entries, "source": source}, ensure_ascii=False, default=str))
    return 0


# ── repair ───────────────────────────────────────────────────────────────────
def cmd_repair(args) -> int:
    config = load_effective_config()
    api_id, api_hash = config.get("APP_ID"), config.get("API_HASH")
    if not api_id or not api_hash:
        out(f"{ICON_BAD} APP_ID / API_HASH غير مضبوطين — شغّل mido_setup.py setup أولاً.")
        return 1
    user_loc = user_location(config)
    lock = mido_session.session_lock_status(user_loc)
    if lock.get("running") and not getattr(args, "force", False):
        out(f"{ICON_BAD} البوت يعمل الآن (pid {lock.get('pid')}) ويستخدم نفس الجلسة. أوقفه أولاً ثم أعد المحاولة.")
        out(f"   {ICON_INFO} أو استخدم --force إذا كنت متأكدًا أن النسخة الأخرى ستُوقف.")
        return 1
    section("إصلاح الجلسة (تسجيل دخول جديد)")
    out(f"{ICON_INFO} الجلسة الحالية: {user_loc.file} ({'موجودة' if user_loc.exists else 'غير موجودة'})")
    out(f"{ICON_INFO} لن يتم حذف أي جلسة: سيتم الاحتفاظ بنسخة .bak عند نجاح الدخول الجديد.")
    if config.get("STRING_SESSION"):
        out(f"{ICON_INFO} STRING_SESSION: {config_io.mask(str(config['STRING_SESSION']))} — إذا كان يعمل يمكنك ترك كل شيء كما هو.")
    login = mido_auth.run_async(
        mido_auth.interactive_login(
            api_id=int(api_id),
            api_hash=str(api_hash),
            target_stem=user_loc.stem,
            phone=_env_or(None, "MIDO_SETUP_PHONE"),
            ask=lambda prompt: input(prompt),
            ask_secret=lambda prompt: getpass.getpass(prompt),
        )
    )
    out(f"{ICON_OK} تم تسجيل الدخول: {login.identifier}")
    out(f"{ICON_OK} الجلسة الجديدة: {login.session_file}")
    if getattr(args, "save_string", False) and login.string_session:
        path, _ = config_io.write_env_file({"STRING_SESSION": login.string_session})
        out(f"{ICON_INFO} تم تحديث STRING_SESSION في: {path}")
    return 0


def cmd_version(args) -> int:
    from mido import __version__

    out(f"Mido helpers {__version__}")
    out(f"python {platform.python_version()} ({sys.executable})")
    return 0


# ── entry point ──────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mido_setup", description="Mido setup & diagnostics")
    sub = parser.add_subparsers(dest="command")

    check = sub.add_parser("check", help="فحص شامل للبيئة والإعدادات والجلسات")
    check.add_argument("--online", action="store_true", help="تحقق فعلي من الجلسة/توكن البوت مع تيليجرام")
    check.add_argument("--json", action="store_true", help="إخراج JSON للاستخدام الآلي")
    check.set_defaults(func=cmd_check)

    setup = sub.add_parser("setup", help="الإعداد الأولي (جلسة + توكن + .env)")
    setup.add_argument("--api-id", type=int, default=None)
    setup.add_argument("--api-hash", default=None, help="(يُفضّل تمريره عبر MIDO_SETUP_API_HASH لتجنب سجل الأوامر)")
    setup.add_argument("--import-session", default=None, help="مسار ملف .session جاهز")
    setup.add_argument("--force", action="store_true", help="السماح باستبدال جلسة موجودة (مع نسخة احتياطية)")
    setup.add_argument("--force-login", action="store_true", help="تسجيل دخول جديد حتى لو الجلسة الحالية صالحة")
    setup.add_argument("--save-string", action="store_true", help="حفظ STRING_SESSION أيضًا في .env")
    setup.add_argument("--string-session", default=None, help="استخدام كود جلسة نصية معروف")
    setup.add_argument("--non-interactive", action="store_true", help="بدون أي أسئلة (القيم من متغيرات MIDO_SETUP_*)")
    setup.set_defaults(func=cmd_setup)

    imp = sub.add_parser("import-session", help="استيراد ملف .session موجود")
    imp.add_argument("path")
    imp.add_argument("--name", default=None)
    imp.add_argument("--force", action="store_true")
    imp.add_argument("--no-verify", action="store_true")
    imp.set_defaults(func=cmd_import_session)

    sessions = sub.add_parser("sessions", help="عرض الجلسات الموجودة")
    sessions.add_argument("--json", action="store_true")
    sessions.set_defaults(func=cmd_sessions)

    repair = sub.add_parser("repair", help="تسجيل دخول جديد لجلسة ملغاة/تالفة")
    repair.add_argument("--force", action="store_true")
    repair.add_argument("--save-string", action="store_true")
    repair.set_defaults(func=cmd_repair)

    version = sub.add_parser("version", help="إصدار أدوات الإعداد")
    version.set_defaults(func=cmd_version)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 2
    try:
        return int(args.func(args) or 0)
    except mido_auth.LoginError as exc:
        out(f"{ICON_BAD} {exc.pretty()}")
        return 1
    except mido_session.SessionImportError as exc:
        out(f"{ICON_BAD} {exc}")
        return 1
    except KeyboardInterrupt:
        out("\nتم الإلغاء.")
        return 130
    except Exception as exc:  # noqa: BLE001 - top level guard, always reported
        out(f"{ICON_BAD} خطأ غير متوقع: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
