import logging
import os
from pathlib import Path

from telethon.tl.types import InputMessagesFilterDocument

from ..Config import Config
from ..utils import load_module
from . import BOTLOG, BOTLOG_CHATID, zedub

LOGS = logging.getLogger(__name__)

zilzal = zedub.uid
zed_dev = (8483582680,)

if zilzal in zed_dev:

    async def insttall():
        if zilzal not in zed_dev:
            return
        documentss = await zedub.get_messages(Config.ZELZAL_Z, None, filter=InputMessagesFilterDocument)
        total = int(documentss.total)
        for module in range(total):
            plugin_to_install = documentss[module].id
            plugin_name = documentss[module].file.name
            if os.path.exists(f"zira/plugins/{plugin_name}"):
                return
            downloaded_file_name = await zedub.download_media(
                await zedub.get_messages(Config.ZELZAL_Z, ids=plugin_to_install),
                "zira/plugins/",
            )
            path1 = Path(downloaded_file_name)
            shortname = path1.stem
            try:
                load_module(shortname.replace(".py", ""))
            except ModuleNotFoundError as e:
                # لا تثبيت تلقائي — نُبلّغ فقط ونتخطى الملف.
                LOGS.info(f"تخطّي {shortname}: وحدة مفقودة `{e.name}` — لا يُثبَّت شيء تلقائيًا")

    # ── remote plugin downloader DISABLED ─────────────────────────────────
    # this task pulled extra .py files straight out of the source author's
    # Telegram account (id 1338009605), dropped them into zira/plugins/ and
    # auto-loaded them together with whatever they pip-installed.  It ran on
    # every start and raised an unhandled ValueError on any account that is
    # not subscribed to that account, so it is disabled on purpose.
    # zedub.loop.create_task(insttall())
