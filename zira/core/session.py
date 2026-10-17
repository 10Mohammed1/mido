import sys
from pathlib import Path

# The `mido` helper package lives next to the `zira` package (repository
# root).  Make sure it is importable no matter where the interpreter was
# started from.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telethon.errors import AccessTokenExpiredError, AccessTokenInvalidError
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged

from mido.session import (
    SessionLockedError,
    acquire_session_lock,
    locate_session,
    resolve_session_dir,
    session_source,
)

from ..Config import Config
from .bothseesion import bothseesion
from .client import ZedUserBotClient
from .logger import logging

LOGS = logging.getLogger("Mido")
__version__ = "2.10.6"

# ── session resolution ───────────────────────────────────────────────────────
# `data/sessions/<SESSION_NAME>.session` is the managed location.  When an
# older deployment still has the file next to the code (the legacy layout) it
# is picked up automatically, so upgrades never log the account out.
_session_dir = resolve_session_dir(getattr(Config, "SESSION_DIR", None))
user_session = locate_session(
    getattr(Config, "SESSION_NAME", None) or "Mido", directory=_session_dir
)
bot_session = locate_session(
    getattr(Config, "BOT_SESSION_NAME", None) or "ZedTgbot", directory=_session_dir
)
_source = session_source(
    getattr(Config, "STRING_SESSION", None),
    prefer=getattr(Config, "SESSION_SOURCE", None),
    file_exists=user_session.exists,
)

if _source == "string":
    session = bothseesion(Config.STRING_SESSION, LOGS)
    LOGS.info("⌔ جلسة المستخدم: STRING_SESSION (نصية)")
else:
    _session_dir.mkdir(parents=True, exist_ok=True)
    session = str(user_session.stem)
    LOGS.info(f"⌔ جلسة المستخدم: ملف {user_session.file}")
    if user_session.legacy:
        LOGS.info(
            "⌔ (نسخة قديمة) الجلسة الموجودة بجوار الكود هي المستخدمة — "
            f"لنقلها لاحقًا إلى {_session_dir} استخدم: python mido_setup.py import-session"
        )

# ── one process per session ─────────────────────────────────────────────────
# Telethon's SQLite sessions are not safe to write from two processes.  A lock
# file next to the session prevents that (stale locks from killed processes
# are replaced automatically).
try:
    SESSION_LOCK = acquire_session_lock(user_session)
except SessionLockedError as _lock_exc:
    print(f"✘ {_lock_exc}")
    sys.exit(1)

try:
    zedub = ZedUserBotClient(
        session=session,
        api_id=Config.APP_ID,
        api_hash=Config.API_HASH,
        app_version=__version__,
        connection=ConnectionTcpAbridged,
        auto_reconnect=True,
        connection_retries=None,
    )
except Exception as e:
    print(
        f"STRING_SESSION CODE WRONG MAKE A NEW SESSION - {e}\n كود سيشن تيليثـون غير صالح .. قم باستخـراج كود جديد ؟!"
    )
    SESSION_LOCK.release()
    sys.exit()


try:
    zedub.tgbot = tgbot = ZedUserBotClient(
        session=str(bot_session.stem),
        api_id=Config.APP_ID,
        api_hash=Config.API_HASH,
        app_version=__version__,
        connection=ConnectionTcpAbridged,
        auto_reconnect=True,
        connection_retries=None,
    ).start(bot_token=Config.TG_BOT_TOKEN)
except AccessTokenExpiredError:
    LOGS.error("توكن البوت غير صالح قم باستبداله بتوكن جديد من بوت فاذر")
except AccessTokenInvalidError:
    LOGS.error("توكن البوت غير صحيح قم باستبداله بتوكن جديد من بوت فاذر")
