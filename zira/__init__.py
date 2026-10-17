import os
import sys

# ── setup / diagnostics routing ──────────────────────────────────────────────
# `python -m zira <setup|check|…>` must run the setup CLI instead of the
# userbot.  runpy imports this package *before* `zira/__main__.py`, so the
# guard has to live here: importing `zira` starts the Telegram clients, which
# is impossible (and unwanted) on a machine that has no session yet.
_CLI_COMMANDS = {"setup", "check", "import-session", "sessions", "repair", "version"}


def _is_cli_invocation() -> bool:
    """True only for ``python -m zira <command>`` (and the direct script run).

    ``import zira`` from an ordinary script must never be hijacked, so the
    check requires both the command name and a runpy/module entry point that
    really belongs to this package.
    """
    if len(sys.argv) < 2 or sys.argv[1] not in _CLI_COMMANDS:
        return False
    argv0 = str(sys.argv[0])
    if argv0 != "-m":  # runpy keeps '-m' while locating the module
        normalized = os.path.abspath(argv0).replace("\\", "/")
        if not normalized.endswith("/zira/__main__.py"):
            return False
    frame = sys._getframe(1)
    while frame is not None:
        if frame.f_code.co_filename in ("<frozen runpy>", "runpy.py"):
            return True
        frame = frame.f_back
    return False


if _is_cli_invocation():
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    from mido.setup_cli import main as _setup_main

    raise SystemExit(_setup_main(sys.argv[1:]))

import signal
import time  # noqa: E402

import heroku3  # noqa: E402

from .Config import Config  # noqa: E402
from .core.logger import logging  # noqa: E402
from .core.session import zedub  # noqa: E402
from .helpers.functions.converter import Convert  # noqa: E402
from .helpers.functions.musictool import *  # noqa: E402,F403
from .helpers.utils.utils import runasync  # noqa: E402
from .sql_helper.globals import addgvar, delgvar, gvarstatus  # noqa: E402

__version__ = "3.3.2"
__license__ = "حقـوق سـورس Mido"
__author__ = "Mido "
__copyright__ = "Mido Source (C) 2020 - 2024  " + __author__

zedub.version = __version__
LOGS = logging.getLogger("Mido")
bot = zedub

StartTime = time.time()
zedversion = "3.3.2"

if Config.UPSTREAM_REPO == "zel":
    UPSTREAM_REPO_URL = "https://github.com/Zilzalll/ZThon"
else:
    UPSTREAM_REPO_URL = Config.UPSTREAM_REPO

if Config.PRIVATE_GROUP_BOT_API_ID == 0:
    if gvarstatus("PRIVATE_GROUP_BOT_API_ID") is None:
        Config.BOTLOG = False
        Config.BOTLOG_CHATID = "me"
    else:
        Config.BOTLOG_CHATID = int(gvarstatus("PRIVATE_GROUP_BOT_API_ID"))
        Config.PRIVATE_GROUP_BOT_API_ID = int(gvarstatus("PRIVATE_GROUP_BOT_API_ID"))
        Config.BOTLOG = True
else:
    if str(Config.PRIVATE_GROUP_BOT_API_ID)[0] != "-":
        Config.BOTLOG_CHATID = int(f"-" + str(Config.PRIVATE_GROUP_BOT_API_ID))
    else:
        Config.BOTLOG_CHATID = Config.PRIVATE_GROUP_BOT_API_ID
    Config.BOTLOG = True

if Config.PM_LOGGER_GROUP_ID == 0:
    if gvarstatus("PM_LOGGER_GROUP_ID") is None:
        Config.PM_LOGGER_GROUP_ID = -100
    else:
        Config.PM_LOGGER_GROUP_ID = int(gvarstatus("PM_LOGGER_GROUP_ID"))
elif str(Config.PM_LOGGER_GROUP_ID)[0] != "-":
    Config.PM_LOGGER_GROUP_ID = int(f"-" + str(Config.PM_LOGGER_GROUP_ID))

try:
    if Config.HEROKU_API_KEY is not None or Config.HEROKU_APP_NAME is not None:
        HEROKU_APP = heroku3.from_key(Config.HEROKU_API_KEY).apps()[
            Config.HEROKU_APP_NAME
        ]
    else:
        HEROKU_APP = None
except Exception:
    HEROKU_APP = None


# Global Configiables
COUNT_MSG = 0
USERS = {}
COUNT_PM = {}
LASTMSG = {}
CMD_HELP = {}
ISAFK = False
AFKREASON = None
CMD_LIST = {}
SUDO_LIST = {}
# for later purposes
INT_PLUG = ""
LOAD_PLUG = {}

# Variables
BOTLOG = Config.BOTLOG
BOTLOG_CHATID = Config.BOTLOG_CHATID
PM_LOGGER_GROUP_ID = Config.PM_LOGGER_GROUP_ID
