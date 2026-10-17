import sys
from pathlib import Path

# ── console encoding ─────────────────────────────────────────────────────────
# The bot prints a lot of Arabic text.  On Windows the console defaults to a
# legacy code page (cp1252/…), which makes those prints raise
# UnicodeEncodeError and kills the process.  Reconfigure - and replace
# unprintable characters instead of crashing.
for _name in ("stdout", "stderr"):
    try:
        getattr(sys, _name).reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── setup / diagnostics commands ─────────────────────────────────────────────
# These run *before* the userbot package is imported: importing `zira` starts
# the Telegram clients and requires a working session, which is exactly what
# a fresh machine does not have yet.
CLI_COMMANDS = {"setup", "check", "import-session", "sessions", "repair", "version"}
if len(sys.argv) > 1 and sys.argv[1] in CLI_COMMANDS:
    _ROOT = Path(__file__).resolve().parent.parent
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    from mido.setup_cli import main as _setup_main

    raise SystemExit(_setup_main(sys.argv[1:]))

import asyncio  # noqa: E402
import zira  # noqa: E402
from zira import BOTLOG_CHATID, HEROKU_APP, PM_LOGGER_GROUP_ID  # noqa: E402
from telethon import functions  # noqa: E402
from .Config import Config  # noqa: E402
from .core.logger import logging  # noqa: E402
from .core.loop import close_loop, get_loop  # noqa: E402
from .core.session import SESSION_LOCK, zedub  # noqa: E402
from .utils import autoname, autovars, mybot, saves  # noqa: E402
from .utils import add_bot_to_logger_group, load_plugins, setup_bot, startupmessage, verifyLoggerGroup  # noqa: E402

LOGS = logging.getLogger("Mido")
cmdhr = Config.COMMAND_HAND_LER

try:
    LOGS.info("⌭ جـارِ تحميـل الملحقـات ⌭")
    get_loop().run_until_complete(autovars())
    LOGS.info("✓ تـم تحميـل الملحقـات .. بنجـاح ✓")
except Exception as e:
    LOGS.error(f"- {e}")

if not Config.ALIVE_NAME:
    try:
        LOGS.info("⌭ بـدء إضافة الاسـم التلقـائـي ⌭")
        get_loop().run_until_complete(autoname())
        LOGS.info("✓ تـم إضافة فار الاسـم .. بـنجـاح ✓")
    except Exception as e:
        LOGS.error(f"- {e}")

try:
    LOGS.info("⌭ بـدء تنزيـل Mido ⌭")
    get_loop().run_until_complete(setup_bot())
    LOGS.info("✓ تـم تنزيـل Mido .. بـنجـاح ✓")
except Exception as e:
    LOGS.error(f"{str(e)}")
    SESSION_LOCK.release()
    sys.exit()

class CatCheck:
    def __init__(self):
        self.sucess = True
Catcheck = CatCheck()

try:
    LOGS.info("⌭ بـدء إنشـاء البـوت التلقـائـي ⌭")
    get_loop().run_until_complete(mybot())
    LOGS.info("✓ تـم إنشـاء البـوت .. بـنجـاح ✓")
except Exception as e:
    LOGS.error(f"- {e}")

try:
    LOGS.info("⌭ الاشتـراك الاجبـاري معطّـل .. تمـام ⌭")
    get_loop().create_task(saves())
    LOGS.info("✓ لا يـوجـد أي اشـتـراك اجـبـاري .. بـنجـاح ✓")
except Exception as e:
    LOGS.error(f"- {e}")


async def startup_process():
    await verifyLoggerGroup()
    await load_plugins("plugins")
    await load_plugins("assistant")
    LOGS.info(f"⌔ تـم تنصيـب Mido . . بنجـاح ✓ \n⌔ لـ إظهـار الاوامـر ارسـل (.الاوامر)")
    await verifyLoggerGroup()
    await add_bot_to_logger_group(BOTLOG_CHATID)
    if PM_LOGGER_GROUP_ID != -100:
        await add_bot_to_logger_group(PM_LOGGER_GROUP_ID)
    await startupmessage()
    Catcheck.sucess = True
    return


get_loop().run_until_complete(startup_process())


def _shutdown() -> None:
    """Close both clients, release the session lock, stop the loop."""
    for client in (getattr(zedub, "tgbot", None), zedub):
        if client is None:
            continue
        try:
            get_loop().run_until_complete(client.disconnect())
        except Exception:
            pass
    try:
        SESSION_LOCK.release()
    except Exception:
        pass
    try:
        close_loop()
    except Exception:
        pass


try:
    if len(sys.argv) not in (1, 3, 4):
        zedub.disconnect()
    elif not Catcheck.sucess:
        if HEROKU_APP is not None:
            HEROKU_APP.restart()
    else:
        try:
            zedub.run_until_disconnected()
        except ConnectionError:
            pass
finally:
    _shutdown()
