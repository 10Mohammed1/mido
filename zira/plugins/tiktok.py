# Mido - Mido
# Copyright (C) 2023 Mido . All Rights Reserved
#
# This file is a part of < https://github.com/Mido/Mido/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/Mido/Mido/blob/zira/LICENSE/>.

import requests
import asyncio
import os
import sys
import urllib.request
from datetime import timedelta
from telethon import events
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetHistoryRequest, ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest as unblock
from telethon.tl.functions.messages import ImportChatInviteRequest as Get

from . import zedub
from ..core.managers import edit_delete, edit_or_reply
from ..helpers import media_type
from ..helpers.utils import reply_id

@zedub.zed_cmd(pattern=f"تيك(?: |$)(.*)")
async def zelzal_tiktok(event):
    malath = event.pattern_match.group(1)
    if malath:
        zelzal = malath
    elif event.is_reply:
        zelzal = await event.get_reply_message()
    else:
        return await edit_or_reply(event, "**⎉╎بالـࢪد ؏ــلى رابـط تيـك تـوك**")
    chat = "@downloader_tiktok_bot"
    zed = await edit_or_reply(event, "**⎉╎جـارِ تحويـل التحميـل من تيـك تـوك ...**")
    async with borg.conversation(chat) as conv:
        try:
            await conv.send_message("/start")
            await conv.get_response()
            await conv.send_message(zelzal)
            zedthon = await conv.get_response()
            await zed.delete()
            await borg.send_file(
                event.chat_id,
                zedthon,
                caption=f"<b>⎉╎تم تحميل الفيديـو .. بنجاح 🎬</b>",
                parse_mode="html",
            )
        except YouBlockedUserError:
            await zedub(unblock("downloader_tiktok_bot"))
            await conv.send_message("/start")
            await conv.get_response()
            await conv.send_message(zelzal)
            zedthon = await conv.get_response()
            await zed.delete()
            await borg.send_file(
                event.chat_id,
                zedthon,
                caption=f"<b>⎉╎تم تحميل الفيديـو .. بنجاح 🎬</b>",
                parse_mode="html",
            )
