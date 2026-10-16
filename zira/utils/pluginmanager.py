import contextlib
import importlib
import sys
from pathlib import Path

from zira import CMD_HELP, LOAD_PLUG

from ..Config import Config
from ..core import LOADED_CMDS, PLG_INFO
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..core.session import zedub
from ..helpers.tools import media_type
from ..helpers.utils import _zedtools, _zedutils, _format, install_pip, reply_id
from .decorators import admin_cmd, sudo_cmd

LOGS = logging.getLogger("Mido")


def load_module(shortname, plugin_path=None):
    if shortname.startswith("__"):
        pass
    elif shortname.endswith("_"):
        path = Path(f"zira/plugins/{shortname}.py")
        checkplugins(path)
        name = "zira.plugins.{}".format(shortname)
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        LOGS.info(f"Successfully imported {shortname}")
    else:
        if plugin_path is None:
            path = Path(f"zira/plugins/{shortname}.py")
            name = f"zira.plugins.{shortname}"
        else:
            path = Path((f"{plugin_path}/{shortname}.py"))
            name = f"{plugin_path}/{shortname}".replace("/", ".")
        checkplugins(path)
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        mod.bot = zedub
        mod.LOGS = LOGS
        mod.Config = Config
        mod._format = _format
        mod.tgbot = zedub.tgbot
        mod.sudo_cmd = sudo_cmd
        mod.CMD_HELP = CMD_HELP
        mod.reply_id = reply_id
        mod.admin_cmd = admin_cmd
        mod._zedutils = _zedutils
        mod._zedtools = _zedtools
        mod.media_type = media_type
        mod.edit_delete = edit_delete
        mod.install_pip = install_pip
        mod.parse_pre = _format.parse_pre
        mod.edit_or_reply = edit_or_reply
        mod.logger = logging.getLogger(shortname)
        mod.borg = zedub
        spec.loader.exec_module(mod)
        # for imports
        sys.modules[f"zira.plugins.{shortname}"] = mod
        LOGS.info(f"Successfully imported {shortname}")


def remove_plugin(shortname):
    try:
        cmd = []
        if shortname in PLG_INFO:
            cmd += PLG_INFO[shortname]
        else:
            cmd = [shortname]
        for cmdname in cmd:
            if cmdname in LOADED_CMDS:
                for i in LOADED_CMDS[cmdname]:
                    zedub.remove_event_handler(i)
                del LOADED_CMDS[cmdname]
        return True
    except Exception as e:
        LOGS.error(e)
    with contextlib.suppress(Exception):
        for i in LOAD_PLUG[shortname]:
            zedub.remove_event_handler(i)
        del LOAD_PLUG[shortname]
    try:
        name = f"zira.plugins.{shortname}"
        for i in reversed(range(len(zedub._event_builders))):
            ev, cb = zedub._event_builders[i]
            if cb.__module__ == name:
                del zedub._event_builders[i]
    except Exception as exc:
        raise ValueError from exc


def checkplugins(filename):
    # ── runtime source rewriting DISABLED ────────────────────────────────
    # This used to open every plugin file, blindly run
    #     .replace("sendmessage", "send_message") ...
    # and write the file back.  Two things were wrong with that:
    #   * it rewrote the whole project on every start (CRLF -> LF, and it
    #     turned the *intended* alias-fix inside تجربة.py into a no-op,
    #     breaking `.تجربة <code>`),
    #   * it silently modified the source tree underneath the operator.
    # The replacements have already been applied to every plugin, so the
    # loader no longer touches files on disk.
    return
