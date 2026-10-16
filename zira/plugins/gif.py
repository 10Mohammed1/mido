# Mido - Mido
# Copyright (C) 2023 Mido . All Rights Reserved
#
# This file is a part of < https://github.com/Mido/Mido/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/Mido/Mido/blob/zira/LICENSE/>.

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

@zedub.zed_cmd(pattern="لمتحركه$")
async def zelzal_gif(event):
    reply_message = await event.get_reply_message()
    if not reply_message or reply_message.text:
        return await edit_or_reply(event, "**- بالـرد ع فيديـو حمبـي 🧸🎈**")
    chat = "@VideoToGifConverterBot"
    zed = await edit_or_reply(event, "**⎉╎جـارِ تحويـل الفيديـو لـ متحـركة ...**")
    async with borg.conversation(chat) as conv:
        try:
            await conv.send_message("/start")
            await conv.get_response()
            await conv.send_file(reply_message)
            await conv.get_response()
            await asyncio.sleep(5)
            zedthon = await conv.get_response()
            await zed.delete()
            await borg.send_file(
                event.chat_id,
                zedthon,
                caption=f"<b>⎉╎تم التحويل لمتحركه .. بنجاح 🎆</b>",
                parse_mode="html",
            )
        except YouBlockedUserError:
            await zedub(unblock("VideoToGifConverterBot"))
            await conv.send_message("/start")
            await conv.get_response()
            await conv.send_file(reply_message)
            await conv.get_response()
            await asyncio.sleep(5)
            zedthon = await conv.get_response()
            await zed.delete()
            await borg.send_file(
                event.chat_id,
                zedthon,
                caption=f"<b>⎉╎تم التحويل لمتحركه .. بنجاح 🎆</b>",
                parse_mode="html",
            )
