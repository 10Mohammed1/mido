# Mido
# Copyright (C) 2022 Mido . All Rights Reserved
#
# This file is a part of < https://github.com/Mido/Mido/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/Mido/Mido/blob/master/LICENSE/>.
#الملـف حقـوق وكتابـة Mido الهيبـه ⤶ @M_O_EG خاص بسـورس ⤶ Mido
#الملـف متعـوب عليه تخمـط اذكر المصـدر
#تخمـط بـدون مصـدر اهينـك

import os
import random
from asyncio import sleep

from telethon.tl.functions.photos import GetUserPhotosRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityMentionName
from telethon.utils import get_input_location

from . import zedub
from ..core.logger import logging

from ..Config import Config
from ..core.managers import edit_or_reply, edit_delete
from ..helpers import reply_id
from . import *
from . import mention

plugin_category = "العروض"
LOGS = logging.getLogger(__name__)

FANAN = "<b> 𓆩 𝗦𝗢𝗨𝗥𝗖𝗘 Mido - 💞🤵💞 𓆪 </b>"
VANAN = "<b>✾╎افيشش 🥺💘 </b>"
sts_fanan = "https://telegra.ph/file/50caf0efa9a2453985364.jpg"
sts_fanan2 = "https://telegra.ph/file/dda7dd09f7d697fe92ff6.jpg" 
sts_fanan3 = "https://telegra.ph/file/007f130ef1028d15c3596.jpg"
sts_fanan4 = "https://telegra.ph/file/593c7e83d4eb25f7b0e55.jpg"
sts_fanan5 = "https://telegra.ph/file/48f567da3417c581446dc.jpg"
sts_fanan6 = "https://telegra.ph/file/165c9405bddc89cf818be.jpg"
sts_fanan7 = "https://telegra.ph/file/7217fc9ebe7c92b1e42c3.jpg"
sts_fanan8 = "hhttps://telegra.ph/file/de70edbf7e01440c6e7bd.jpg"
sts_fanan9 = "https://telegra.ph/file/63e1b87537e92c05da46d.jpg"
sts_fanan10 = "https://telegra.ph/file/d58d68c118d862437f66a.jpg"
sts_fanan11 = "https://telegra.ph/file/28c209102abe082b97e99.jpg"
sts_fanan12 = "https://telegra.ph/file/53f4c117abcfc24934337.jpg"
sts_fanan13 = "https://telegra.ph/file/739a13b944c62412e908b.jpg"
sts_fanan14 = "https://telegra.ph/file/291a667b5bc7e7f15895d.jpg"
sts_fanan15 = "https://telegra.ph/file/e83874718d4eb829fc0e7.jpg"
sts_fanan16 = "https://telegra.ph/file/f2683a9c2f6aec9f16850.jpg"
sts_fanan17 = "https://telegra.ph/file/8775bf7b8edde56243897.jpg"
sts_fanan18 = "https://telegra.ph/file/b544499b6853568ce475f.jpg"
zahff = "https://t.me/fasngon/287"
gtg_fanan = "https://telegra.ph/file/1f79aad6235f08ea76166.jpg"
gtg_fanan2 = "https://telegra.ph/file/e04b22171d7bb524e7f44.jpg" 
gtg_fanan3 = "https://telegra.ph/file/4502e1268a73117d9abac.jpg"
gtg_fanan4 = "https://telegra.ph/file/5221a638913c64749760b.jpg"
gtg_fanan5 = "https://telegra.ph/file/9c070eb80b621cbe0333c.jpg"
gtg_fanan6 = "https://telegra.ph/file/6f34aa7f98fb6cfec3b57.jpg"
gtg_fanan7 = "https://telegra.ph/file/9f0de560d7e7fc2752437.jpg"
gtg_fanan8 = "https://telegra.ph/file/434d739dd887df9a40ae1.jpg"
gtg_fanan9 = "https://telegra.ph/file/ac11888f2eca8529387de.jpg"
gtg_fanan10 = "https://telegra.ph/file/4d999ac0dddd3964979a4.jpg"
gtg_fanan11 = "https://telegra.ph/file/07d59b7a9a9b37c46d64f.jpg"
gtg_fanan12 = "https://telegra.ph/file/788aab2a68a5a6f19f8c1.jpg"
gtg_fanan13 = "https://telegra.ph/file/6c18a61f0f3d9e5b51576.jpg"
gtg_fanan14 = "https://telegra.ph/file/974240259ba3d35a0507d.jpg"
gtg_fanan15 = "https://telegra.ph/file/a5d73c57e8eea74937093.jpg"
gtg_fanan16 = "https://telegra.ph/file/e6fd5618dc186ae286e9c.jpg"
gtg_fanan17 = "https://telegra.ph/file/d40c3f57c3b1c2fceaef0.jpg"
gtg_fanan18 = "https://telegra.ph/file/650f99255eb90e8f95061.jpg"

GZED_IMG = gtg_fanan or gtg_fanan2 or gtg_fanan3 or gtg_fanan4 or gtg_fanan5
ZEED_IMG = sts_fanan or sts_fanan2 or sts_fanan3 or sts_fanan4 or sts_fanan5
ZED_VOICE = zahff


async def get_user_from_event(event):
    if event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        user_object = await event.client.get_entity(previous_message.sender_id)
    else:
        user = event.pattern_match.group(1)
        if user.isnumeric():
            user = int(user)
        if not user:
            self_user = await event.client.get_me()
            user = self_user.id
        if event.message.entities:
            probable_user_mention_entity = event.message.entities[0]
            if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                user_obj = await event.client.get_entity(user_id)
                return user_obj
        if isinstance(user, int) or user.startswith("@"):
            user_obj = await event.client.get_entity(user)
            return user_obj
        try:
            user_object = await event.client.get_entity(user)
        except (TypeError, ValueError) as err:
            await event.edit(str(err))
            return None
    return user_object


async def zfetch_info(replied_user, event):
    """Get details from the User object."""
    FullUser = (await event.client(GetFullUserRequest(replied_user.id))).full_user
    user_id = replied_user.id
    first_name = replied_user.first_name
    last_name = replied_user.last_name
    full_name = FullUser.private_forward_name
    common_chat = FullUser.common_chats_count
    username = replied_user.username
    user_bio = FullUser.about
    is_bot = replied_user.bot
    restricted = replied_user.restricted
    verified = replied_user.verified
    ZED_VOICE
    x = random.randrange(1, 2)
    if x == 1:
       caption = f"<b>⪼• اطـلـع زاحـف 😹🤫</b>\n\n"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return zahff, caption
    if x == 2:
       caption = f"<b>⪼• اطـلـع زاحـف 😹🤫</b>\n\n"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return zahff, caption


async def fetch_info(replied_user, event):
    """Get details from the User object."""
    FullUser = (await event.client(GetFullUserRequest(replied_user.id))).full_user
    user_id = replied_user.id
    first_name = replied_user.first_name
    last_name = replied_user.last_name
    full_name = FullUser.private_forward_name
    common_chat = FullUser.common_chats_count
    username = replied_user.username
    user_bio = FullUser.about
    is_bot = replied_user.bot
    restricted = replied_user.restricted
    verified = replied_user.verified
    ZEED_IMG
    x = random.randrange(1, 18)
    if x == 1:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن إنجين أكيوريك 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan, caption
    if x == 2:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن كيفانش تاتليتوغ 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan2, caption
    if x == 3:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن شاتاي أولسوي 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan3, caption
    if x == 4:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن إنجين ألتان دوزياتان 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan4, caption
    if x == 5:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن بوراك أوزجيفت 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan5, caption
    if x == 6:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن أراس بولوت إيناملي 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan6, caption
    if x == 7:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن گريستيانو رونالدو 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan7, caption
    if x == 8:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن سيركان شاي أوغلو 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan8, caption
    if x == 9:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن كرم بورسين🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan9, caption
    if x == 10:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن توم گــروز🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan10, caption
    if x == 11:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن شاهـد گــابور🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan11, caption
    if x == 12:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن ليـو ميسـي🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan12, caption
    if x == 13:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن محمد حماقي🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan13, caption
    if x == 14:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن شَاروخــان🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan14, caption
    if x == 15:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن سيـف نبيل🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan15, caption
    if x == 16:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن ليوناردو گـابريو 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan16, caption
    if x == 17:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن محمد رمـضان🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan17, caption
    if x == 18:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجج مِـن سعــد المجرد 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return sts_fanan18, caption


async def ifetch_info(replied_user, event):
    """Get details from the User object."""
    FullUser = (await event.client(GetFullUserRequest(replied_user.id))).full_user
    user_id = replied_user.id
    first_name = replied_user.first_name
    last_name = replied_user.last_name
    full_name = FullUser.private_forward_name
    common_chat = FullUser.common_chats_count
    username = replied_user.username
    user_bio = FullUser.about
    is_bot = replied_user.bot
    restricted = replied_user.restricted
    verified = replied_user.verified
    GZED_IMG
    x = random.randrange(1, 18)
    if x == 1:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن بيرين سات 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan, caption
    if x == 2:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن إسـراء الاصيـل 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan2, caption
    if x == 3:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن رحمـة ريـاض 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan3, caption
    if x == 4:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن تـوبا بويوكـوستن 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan4, caption
    if x == 5:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن هـازال كـايا 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan5, caption
    if x == 6:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن هـاندا ارتشـل 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan6, caption
    if x == 7:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن هيفـاء وهبـي 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan7, caption
    if x == 8:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن نانسـي عجـرم 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan8, caption
    if x == 9:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن شيـرين عبد الوهـاب 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan9, caption
    if x == 10:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن احـلام 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan10, caption
    if x == 11:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن حـلا تـرك 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan11, caption
    if x == 12:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن نجـوى كـرم 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan12, caption
    if x == 13:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن هـاندا ارتشـل 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan13, caption
    if x == 14:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن آيشـه افيخـاي 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan14, caption
    if x == 15:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن burcu ozberk 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan15, caption
    if x == 16:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن شيمـاء سيـف 😂💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan16, caption
    if x == 17:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن نيهـان اتاغـول 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan17, caption
    if x == 18:
       caption = f"<b> {FANAN} </b>\n\n\n"
       caption += f"<b> {VANAN} </b>"
       caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'
       caption += f"\n\n<b> ✾╎مبࢪوڪ زواجك مِـن ميليسـا بامـوك 🥺💘. </b>"
       caption += f"\n\n<b> 𓆩 𝙎𝙊𝙐𝙍𝘾𝞝 Mido 𓆪 </b> - @Mido "
       return gtg_fanan18, caption


@zedub.zed_cmd(pattern="مشهور(?: |$)(.*)")
async def who(event):
    zed = await edit_or_reply(event, "⇆")
    if not os.path.isdir(Config.TMP_DOWNLOAD_DIRECTORY):
        os.makedirs(Config.TMP_DOWNLOAD_DIRECTORY)
    replied_user = await get_user_from_event(event)
    try:
        ZEED_IMG, caption = await fetch_info(replied_user, event)
    except AttributeError:
        return await edit_or_reply(zed, "**- لـم استطـع العثــور ع الشخــص**")
    message_id_to_reply = event.message.reply_to_msg_id
    if not message_id_to_reply:
        message_id_to_reply = None
    try:
        await event.client.send_file(
            event.chat_id,
            ZEED_IMG,
            caption=caption,
            link_preview=False,
            force_document=False,
            reply_to=message_id_to_reply,
            parse_mode="html",
        )
        await zed.delete()
    except TypeError:
        await zed.edit(caption, parse_mode="html")


@zedub.zed_cmd(pattern="مشهوره(?: |$)(.*)")
async def who(event):
    zed = await edit_or_reply(event, "⇆")
    if not os.path.isdir(Config.TMP_DOWNLOAD_DIRECTORY):
        os.makedirs(Config.TMP_DOWNLOAD_DIRECTORY)
    replied_user = await get_user_from_event(event)
    try:
        GZED_IMG, caption = await ifetch_info(replied_user, event)
    except AttributeError:
        return await edit_or_reply(zed, "**- لـم استطـع العثــور ع الشخــص**")
    message_id_to_reply = event.message.reply_to_msg_id
    if not message_id_to_reply:
        message_id_to_reply = None
    try:
        await event.client.send_file(
            event.chat_id,
            GZED_IMG,
            caption=caption,
            link_preview=False,
            force_document=False,
            reply_to=message_id_to_reply,
            parse_mode="html",
        )
        await zed.delete()
    except TypeError:
        await zed.edit(caption, parse_mode="html")


@zedub.zed_cmd(pattern="زاحف(?: |$)(.*)")
async def who(event):
    zed = await edit_or_reply(event, "⇆")
    if not os.path.isdir(Config.TMP_DOWNLOAD_DIRECTORY):
        os.makedirs(Config.TMP_DOWNLOAD_DIRECTORY)
    replied_user = await get_user_from_event(event)
    try:
        ZEED_IMG, caption = await zfetch_info(replied_user, event)
    except AttributeError:
        return await edit_or_reply(zed, "**- لـم استطـع العثــور ع الشخــص**")
    message_id_to_reply = event.message.reply_to_msg_id
    if not message_id_to_reply:
        message_id_to_reply = None
    try:
        await event.client.send_file(
            event.chat_id,
            ZED_VOICE,
            caption=caption,
            link_preview=False,
            force_document=False,
            reply_to=message_id_to_reply,
            parse_mode="html",
        )
        await zed.delete()
    except TypeError:
        await zed.edit(caption, parse_mode="html")


