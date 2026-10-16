# Mido
# Copyright (C) 2023 Mido . All Rights Reserved
#
# This file is a part of < https://github.com/Mido/Mido/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/Mido/Mido/blob/main/LICENSE/>.
"""سـورس Mido ™
So تخمـط الملـف اهينك واطشك للناس خماط واوثق عليك
Copyright (C) 2023 Mido . All Rights Reserved
Credit: https://github.com/Mido/Mido
Devloper:  - Mido الهيبــه"""
"""import json
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
from telethon.tl.functions.users import GetUsersRequest

from . import zedub
from ..Config import Config
from ..helpers import reply_id
from ..sql_helper.globals import gvarstatus
from ..core.logger import logging
from ..helpers.utils import _format
from . import mention

LOGS = logging.getLogger(__name__)
tr = Config.COMMAND_HAND_LER

# Copyright (C) 2023 Mido . All Rights Reserved
@zedub.tgbot.on(InlineQuery)
async def inline_handler(event):
    from .ziiz import ttt, ddd, bbb, hmm, ymm, fmm, dss, hss, nmm, mnn, bmm, scc
    builder = event.builder
    result = None
    query = event.text
    string = query.lower()
    query.split(" ", 2)
    str_y = query.split(" ", 1)
    string.split()
    query_user_id = event.query.user_id
    user_id = gvarstatus("hmsa_id")
    full_name = gvarstatus("hmsa_name")
    username = gvarstatus("hmsa_user")
    if username.startswith("@"):
        Mido = gvarstatus("hmsa_user")
    else:
        Mido = f"[{full_name}](tg://user?id={user_id})"
    if query_user_id == Config.OWNER_ID or query_user_id in Config.SUDO_USERS:
        malathid = Config.OWNER_ID
    elif query_user_id == user_id or query_user_id == int(user_id):
        malathid = user_id
    if query_user_id == Config.OWNER_ID or query_user_id == user_id or query_user_id == int(user_id) or query_user_id in Config.SUDO_USERS:
        inf = re.compile("secret (.*) (.*)")
        match2 = re.findall(inf, query)
        if match2:
            user_list = []
            Mido = ""
            query = query[7:]
            info_type = [hmm, ymm, fmm]
            if "|" in query:
                iris, query = query.replace(" |", "|").replace("| ", "|").split("|")
                users = iris.split(" ")
            else:
                user, query = query.split(" ", 1)
                users = [user]
            for user in users:
                usr = int(user) if user.isdigit() else user
                try:
                    u = await zedub.get_entity(usr)
                except ValueError:
                    u = await zedub(GetUsersRequest(usr))
                if u.username:
                    Mido += f"@{u.username}"
                else:
                    Mido += f"[{u.first_name}](tg://user?id={u.id})"
                user_list.append(u.id)
                Mido += " "
            Mido = Mido[:-1]
            old_msg = os.path.join("./zira", f"{scc}.txt")
            try:
                jsondata = json.load(open(old_msg))
            except Exception:
                jsondata = False
            timestamp = int(time.time() * 2)
            new_msg = {
                str(timestamp): {"userid": user_list, "text": query}
            }
            buttons = [[Button.inline(info_type[2], data=f"{scc}_{timestamp}")],[Button.switch_inline(bmm, query=f"secret {malathid} \nهلو", same_peer=True)]]
            result = builder.article(
                title=f"{hmm} {Mido}",
                description=f"{dss}",
                text=f"{hss} {Mido} \n**{dss}**",
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
                    title=f"{nmm}",
                    description=f"{mnn}",
                    text=f"**{ttt}** {Mido} **{ddd}**",
                    buttons=bbb,
                    link_preview=False,
                ),
            )
            await event.answer(results)
"""
