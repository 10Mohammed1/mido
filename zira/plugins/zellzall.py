# Mido
# Copyright (C) 2022 Mido . All Rights Reserved
#
# This file is a part of < https://github.com/Mido/Mido/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/Mido/Mido/blob/main/LICENSE/>.
import json
import math
import asyncio
import os
import random
import re
import time
from pathlib import Path
from uuid import uuid4

from telethon import Button, types
from telethon.errors import QueryIdInvalidError
from telethon.events import CallbackQuery, InlineQuery

from . import zedub

from ..Config import Config
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from ..core.logger import logging
from ..core import check_owner, pool
from ..helpers.utils import _format
from . import mention
LOGS = logging.getLogger(__name__)
tr = Config.COMMAND_HAND_LER

plugin_category = "البوت"

# Copyright (C) 2022 Mido . All Rights Reserved
@zedub.tgbot.on(InlineQuery)
async def inline_handler(event):  # sourcery no-metrics
    try:  # the upstream source ships this module missing; degrade gracefully
        from .hhh import aaa, bbb
    except ImportError:
        return
    builder = event.builder
    result = None
    query = event.text
    string = query.lower()
    query.split(" ", 2)
    str_y = query.split(" ", 1)
    string.split()
    query_user_id = event.query.user_id
    ussr = int(aaa) if aaa.isdigit() else aaa  # by @M_O_EG
    try:
        zzz = await event.client.get_entity(ussr)
    except ValueError:
        return
    zelzal = f"[{zzz.first_name}](tg://user?id={zzz.id})"
    if query_user_id == Config.OWNER_ID or query_user_id in Config.SUDO_USERS:  # by @M_O_EG
        malathid = Config.OWNER_ID
    elif query_user_id == zzz.id:
        malathid = zzz.id
    if query_user_id == Config.OWNER_ID or query_user_id == zzz.id or query_user_id in Config.SUDO_USERS:  # by @M_O_EG
        inf = re.compile("secret (.*) (.*)")
        match2 = re.findall(inf, query)
        if match2:
            user_list = []
            zilzal = ""
            query = query[7:]
            info_type = ["secret", "يستطيـع", "فتـح الهمسـه 🗳"]
            zed_type = ["همسـة", "يستطيـع", "فتـح الهمسـه 🗳"]
            if "|" in query:
                iris, query = query.replace(" |", "|").replace("| ", "|").split("|")
                users = iris.split(" ")
            else:
                user, query = query.split(" ", 1)
                users = [user]
            for user in users:
                usr = int(user) if user.isdigit() else user
                try:
                    u = await event.client.get_entity(usr)
                except ValueError:
                    return
                if u.username:
                    zilzal += f"@{u.username}"
                else:
                    zilzal += f"[{u.first_name}](tg://user?id={u.id})"
                user_list.append(u.id)
                zilzal += " "
            zilzal = zilzal[:-1]
            old_msg = os.path.join("./zira", f"{info_type[0]}.txt")
            try:
                jsondata = json.load(open(old_msg))
            except Exception:
                jsondata = False
            timestamp = int(time.time() * 2)
            new_msg = {
                str(timestamp): {"userid": user_list, "text": query}
            }  # by @M_O_EG
            buttons = [[Button.inline(info_type[2], data=f"{info_type[0]}_{timestamp}")],[Button.switch_inline("اضغـط للـرد", query=f"secret {malathid} \nهلو", same_peer=True)]]
            result = builder.article(
                title=f"{info_type[0].title()} سـࢪيـه الـى {zilzal}.",
                description=f"هـو فقـط مـن {info_type[1]} ࢪؤيتهـا.",
                text=f"ᯓ 𝗦𝗢𝗨𝗥𝗖𝗘 Mido - همسـة سـࢪيـه 📠\n⋆┄─┄─┄─┄┄─┄─┄─┄─┄┄⋆\n\n**⌔╎الهمسـة لـ** {zilzal} \n**⌔╎هو فقط من يستطيع ࢪؤيتهـا**",
                buttons=buttons,
                link_preview=False,
            )
            await event.answer([result] if result else None)
            if jsondata:
                jsondata.update(new_msg)
                json.dump(jsondata, open(old_msg, "w"))
            else:
                json.dump(new_msg, open(old_msg, "w"))
        elif string == "Mido":
            results = []
            results.append(
                builder.article(
                    title="همسـه سريـه",
                    description="ارسـال همسـه سريـه لـ (شخـص/اشخـاص).\nادخـل : secret + يوزر + نـص",
                    text=f"ᯓ 𝗦𝗢𝗨𝗥𝗖𝗘 Mido **- همسـة سـࢪيـه**\n⋆┄─┄─┄─┄┄─┄─┄─┄─┄┄⋆\n\n**⌔╎اضغـط 🚹**\n**⌔╎لـ اࢪسـال همسـه سـࢪيـه الى** {zelzal} 💌\n**⌔╎او اضغـط 🛗**\n**⌔╎لـ اࢪسـال همسـه جماعية الى الشخص وأشخـاص آخرون 📨**",
                    buttons=bbb,
                    link_preview=False,
                ),
            )
            await event.answer(results)
