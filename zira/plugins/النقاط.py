import requests
import asyncio
import time
import re
from telethon import events
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.users import GetFullUserRequest

from . import zedub
from ..Config import Config
from ..core.managers import edit_delete, edit_or_reply
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from ..helpers.utils import reply_id
estithmar = False
ratp = False
thifts = False
bahsees = False

ZelzalCoins_cmd = (
    "ᯓ 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - اوامـر تجميـع النقـاط 𓆪\n\n"
    "**⎉╎قـائمـة اوامـر تجميـع نقـاط بوتـات تمـويـل الخاص بسـورس Mido🦾 :** \n\n"
    "`.المليار`\n"
    "**⪼ لـ تجميـع النقـاط مـن بـوت المليـار ( @EEOBot ) .. تلقـائيـاً ✓**\n\n"
    "`.العرب`\n"
    "**⪼ لـ تجميـع النقـاط مـن بـوت العـرب ( @xnsex21bot ) .. تلقـائيـاً ✓**\n\n"
    "`.دعمكم`\n"
    "**⪼ لـ تجميـع النقـاط مـن بـوت دعمكـم ( @DamKombot ) .. تلقـائيـاً ✓**\n\n"
    "`.الجوكر`\n"
    "**⪼ لـ تجميـع النقـاط مـن بـوت الجوكـر ( @A_MAN9300BOT ) .. تلقـائيـاً ✓**\n\n"
    "`.الجنرال`\n"
    "**⪼ لـ تجميـع النقـاط مـن بـوت العقــاب ( @MARKTEBOT ) .. تلقـائيـاً ✓**\n\n"
    "`.المليون`\n"
    "**⪼ لـ تجميـع النقـاط مـن بـوت المليــون ( @qweqwe1919bot ) .. تلقـائيـاً ✓**\n\n\n"
    "`.سمسم`\n"
    "**⪼ لـ تجميـع النقـاط مـن بـوت سمـسـم ( @SMSMWAbot ) .. تلقـائيـاً ✓**\n\n\n"
    "`.تناهيد`\n"
    "**⪼ لـ تجميـع النقـاط مـن بـوت تناهيـد ( @Ncoe_bot ) .. تلقـائيـاً ✓**\n\n"
    "`.المليار ايقاف`\n"
    "**⪼ لـ ايقـاف عمليـة تجميـع النقـاط من بوت المليـار ..**\n\n"
    "`.الجوكر ايقاف`\n"
    "**⪼ لـ ايقـاف عمليـة تجميـع النقـاط من بوت الجوكـر ..**\n\n"
    "`.العرب ايقاف`\n"
    "**⪼ لـ ايقـاف عمليـة تجميـع النقـاط من بوت العـرب ..**\n\n"
    "`.العقاب ايقاف`\n"
    "**⪼ لـ ايقـاف عمليـة تجميـع النقـاط من بوت العقـاب ..**\n\n"
    "`.المليون ايقاف`\n"
    "**⪼ لـ ايقـاف عمليـة تجميـع النقـاط من بوت المليـون ..**\n\n"
    "`.سمسم ايقاف`\n"
    "**⪼ لـ ايقـاف عمليـة تجميـع النقـاط من بوت سمـسـم ..**\n\n"
    "`.تناهيد ايقاف`\n"
    "**⪼ لـ ايقـاف عمليـة تجميـع النقـاط من بوت تناهيـد ..**\n\n\n"
    "`.اضف بوت التجميع`\n"
    "**⪼ بالـرد ع معـرف البـوت الجديـد لـ اضافته لـ السـورس ..**\n\n"
    "`.تجميع`\n"
    "**⪼ لـ تجميـع النقـاط مـن البـوت المضاف لـ الفـارات .. تلقـائيـاً ✓**\n\n"
    "`.تجميع ايقاف`\n"
    "**⪼ لـ ايقـاف عمليـة تجميـع النقـاط من البوت المضاف للفـارات ..**\n\n"
    "`.بوت التجميع`\n"
    "**⪼ لـ عـرض بوت التجميـع المضـاف لـ الفـارات ..**\n\n\n"
    "**⎉╎قـائمـة اوامـر تجميـع نقـاط العـاب بـوت وعـد🦾 :** \n\n"
    "`.بخشيش وعد`\n"
    "`.راتب وعد`\n"
    "`.استثمار وعد`\n"
    "`.كلمات وعد`\n"
    "**⪼ لـ تجميـع نقـاط العـاب في بوت وعـد تلقائيـاً ✓ ..قم بـ اضافة البوت في مجموعة جديدة ثم ارسل**\n"
    "**الامـر + عـدد الاعـادة للامـر**\n"
    "**⪼ مثــال :**\n"
    "`.راتب وعد 50`\n\n\n"
    "**- مـلاحظــه :**\n"
    "**⪼ سيتم اضـافـه المزيـد من البوتـات بالتحديثـات الجايـه .. اذا تريـد اضافـة بـوت محـدد راسـل مطـور السـورس @M_O_EG**"
)

@zedub.zed_cmd(pattern="بوت المليار$")
async def _(event):
    await event.edit('@EEOBot')

# Copyright (C) 2022 Mido . All Rights Reserved
@zedub.zed_cmd(pattern="(المليار|تجميع المليار)(?: |$)(.*)")

async def _(event):
    con = event.pattern_match.group(1).lower()
    await event.edit("**⎉╎حسنـاً .. تأكـد من انك مشتـرك بـ قنـوات الاشتـراك الاجبـاري لتجنب الأخطـاء @EEOBot**")
    channel_entity = await zedub.get_entity('@EEOBot')
    await zedub.send_message('@EEOBot', '/start')
    await asyncio.sleep(4)
    msg0 = await zedub.get_messages('@EEOBot', limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await zedub.get_messages('@EEOBot', limit=1)
    await msg1[0].click(0)
    chs = 1
    for i in range(100):
        await asyncio.sleep(10)
        list = await zedub(GetHistoryRequest(peer=channel_entity, limit=1, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('**⎉╎لا يوجد قنوات في الوقت الحالي .. قم يتجميع النقاط بطريقه مختلفه**') != -1:
            await zedub.send_message(event.chat_id, "**⎉╎مـافي قنـوات بالبـوت حاليـاً ...**")
            break
        if con == "ايقاف":
            await zedub.send_message(event.chat_id, "**⎉╎تم إيقـاف تجميـع النقـاط .. بنجـاح☑️**")
            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await zedub(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await zedub(ImportChatInviteRequest(bott))
            msg2 = await zedub.get_messages('@EEOBot', limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**⎉╎تم الاشتـراك في القنـاة  {chs} ...✓**")
        except:
            msg2 = await zedub.get_messages('@EEOBot', limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**⎉╎القنـاة رقـم {chs} .. يمكـن تبنـدت**")
    await zedub.send_message(event.chat_id, "**⎉╎تم الانتهـاء مـن تجميـع النقـاط .. حاول من جديد في وقت آخر ✓**")

@zedub.zed_cmd(pattern="بوت العرب$")
async def _(event):
    await event.edit('@xnsex21bot')

@zedub.zed_cmd(pattern="(العرب|تجميع العرب)(?: |$)(.*)")
async def _(event):
    con = event.pattern_match.group(1).lower()
    await event.edit("**⎉╎حسنـاً .. تأكـد من انك مشتـرك بـ قنـوات الاشتـراك الاجبـاري لتجنب الأخطـاء @xnsex21bot**")
    channel_entity = await zedub.get_entity('@xnsex21bot')
    await zedub.send_message('@xnsex21bot', '/start')
    await asyncio.sleep(4)
    msg0 = await zedub.get_messages('@xnsex21bot', limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await zedub.get_messages('@xnsex21bot', limit=1)
    await msg1[0].click(0)
    chs = 1
    for i in range(100):
        await asyncio.sleep(10)
        list = await zedub(GetHistoryRequest(peer=channel_entity, limit=1, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('**⎉╎لا يوجد قنوات في الوقت الحالي .. قم يتجميع النقاط بطريقه مختلفه**') != -1:
            await zedub.send_message(event.chat_id, "**⎉╎مـافي قنـوات بالبـوت حاليـاً ...**")
            break
        if con == "ايقاف":
            await zedub.send_message(event.chat_id, "**⎉╎تم إيقـاف تجميـع النقـاط .. بنجـاح☑️**")
            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await zedub(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await zedub(ImportChatInviteRequest(bott))
            msg2 = await zedub.get_messages('@xnsex21bot', limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**⎉╎تم الاشتـراك في القنـاة  {chs} ...✓**")
        except:
            msg2 = await zedub.get_messages('@xnsex21bot', limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**⎉╎القنـاة رقـم {chs} .. يمكـن تبنـدت**")
    await zedub.send_message(event.chat_id, "**⎉╎تم الانتهـاء مـن تجميـع النقـاط .. حاول من جديد في وقت آخر ✓**")

@zedub.zed_cmd(pattern="بوت التجميع$")
async def _(event):
    zpoint = gvarstatus("Z_Point")
    if gvarstatus("Z_Point") is None:
        await event.edit("**⎉╎لايوجـد بوت تجميع مضاف بعـد ؟!**\n\n**⎉╎لـ اضافة بوت تجميع جديد**\n**⎉╎ارسـل**  `.اضف بوت التجميع`  **بالـرد ع معـرف البـوت**")
    else:
        await event.edit(f"**⎉╎بوت التجميـع المضـاف حاليـاً**\n**⎉╎هـو** {zpoint}")

# Copyright (C) 2022 Mido . All Rights Reserved
@zedub.zed_cmd(pattern="تجميع(?: |$)(.*)")
async def _(event):
    con = event.pattern_match.group(1).lower()
    zpoint = gvarstatus("Z_Point")
    if con in ("المليار", "الجوكر", "الجنرال", "العقاب", "المليون", "سمسم", "تناهيد", "العرب"):
        return await event.edit("**⎉╎عـذراً .. عـزيـزي امـر خاطـئ .\n⎉╎لـ رؤيـة اوامـر التجميـع ارسـل**\n\n`.اوامر التجميع`")
    if gvarstatus("Z_Point") is None:
        return await event.edit("**⎉╎لايوجـد بـوت تجميـع مضـاف للفـارات ؟!\n⎉╎لـ اضافة بـوت تجميـع\n⎉╎ارسـل** `.اضف بوت التجميع` **بالـرد ع معـرف البـوت\n\n⎉╎او استخـدم امر تجميع** `.المليار`")
    await event.edit(f"**⎉╎حسنـاً .. تأكـد من انك مشتـرك بـ قنـوات الاشتـراك الاجبـاري لتجنب الأخطـاء {zpoint} .**")
    channel_entity = await zedub.get_entity(zpoint)
    await zedub.send_message(zpoint, '/start')
    await asyncio.sleep(4)
    msg0 = await zedub.get_messages(zpoint, limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await zedub.get_messages(zpoint, limit=1)
    await msg1[0].click(0)
    chs = 1
    for i in range(100):
        await asyncio.sleep(10)
        list = await zedub(GetHistoryRequest(peer=channel_entity, limit=1, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('**⎉╎لا يوجد قنوات في الوقت الحالي .. قم يتجميع النقاط بطريقه مختلفه**') != -1:
            await zedub.send_message(event.chat_id, "**⎉╎مـافي قنـوات بالبـوت حاليـاً ...**")
            break
        if con == "ايقاف":
            await zedub.send_message(event.chat_id, "**⎉╎تم إيقـاف تجميـع النقـاط .. بنجـاح☑️**")
            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await zedub(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await zedub(ImportChatInviteRequest(bott))
            msg2 = await zedub.get_messages(zpoint, limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**⎉╎تم الاشتـراك في القنـاة  {chs} ...✓**")
        except:
            msg2 = await zedub.get_messages(zpoint, limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**⎉╎القنـاة رقـم {chs} .. يمكـن تبنـدت**")
    await zedub.send_message(event.chat_id, "**⎉╎تم الانتهـاء مـن تجميـع النقـاط .. حاول من جديد في وقت آخر ✓**")

@zedub.zed_cmd(pattern="بوت الجوكر$")
async def _(event):
    await event.edit('@A_MAN9300BOT')

# Copyright (C) 2022 Mido . All Rights Reserved
@zedub.zed_cmd(pattern="(الجوكر|تجميع الجوكر)(?: |$)(.*)")
async def _(event):
    con = event.pattern_match.group(1).lower()
    await event.edit("**⎉╎حسنـاً .. تأكـد من انك مشتـرك بـ قنـوات الاشتـراك الاجبـاري لتجنب الأخطـاء @A_MAN9300BOT**")
    channel_entity = await zedub.get_entity('@A_MAN9300BOT')
    await zedub.send_message('@A_MAN9300BOT', '/start')
    await asyncio.sleep(4)
    msg0 = await zedub.get_messages('@A_MAN9300BOT', limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await zedub.get_messages('@A_MAN9300BOT', limit=1)
    await msg1[0].click(0)
    chs = 1
    for i in range(100):
        await asyncio.sleep(10)
        list = await zedub(GetHistoryRequest(peer=channel_entity, limit=1, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('**⎉╎لا يوجد قنوات في الوقت الحالي .. قم يتجميع النقاط بطريقه مختلفه**') != -1:
            await zedub.send_message(event.chat_id, "**⎉╎مـافي قنـوات بالبـوت حاليـاً ...**")
            break
        if con == "ايقاف":
            await zedub.send_message(event.chat_id, "**⎉╎تم إيقـاف تجميـع النقـاط .. بنجـاح☑️**")
            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await zedub(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await zedub(ImportChatInviteRequest(bott))
            msg2 = await zedub.get_messages('@A_MAN9300BOT', limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**⎉╎تم الاشتـراك في القنـاة  {chs} ...✓**")
        except:
            msg2 = await zedub.get_messages('@A_MAN9300BOT', limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**⎉╎القنـاة رقـم {chs} .. يمكـن تبنـدت**")
    await zedub.send_message(event.chat_id, "**⎉╎تم الانتهـاء مـن تجميـع النقـاط .. حاول من جديد في وقت آخر ✓**")

@zedub.zed_cmd(pattern="بوت الجنرال$")
async def _(event):
    await event.edit('@MARKTEBOT')

# Copyright (C) 2022 Mido . All Rights Reserved
@zedub.zed_cmd(pattern="(الجنرال|تجميع الجنرال)(?: |$)(.*)")
async def _(event):
    con = event.pattern_match.group(1).lower()
    await event.edit("**⎉╎حسنـاً .. تأكـد من انك مشتـرك بـ قنـوات الاشتـراك الاجبـاري لتجنب الأخطـاء @MARKTEBOT**")
    channel_entity = await zedub.get_entity('@MARKTEBOT')
    await zedub.send_message('@MARKTEBOT', '/start')
    await asyncio.sleep(4)
    msg0 = await zedub.get_messages('@MARKTEBOT', limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await zedub.get_messages('@MARKTEBOT', limit=1)
    await msg1[0].click(0)
    chs = 1
    for i in range(100):
        await asyncio.sleep(10)
        list = await zedub(GetHistoryRequest(peer=channel_entity, limit=1, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('**⎉╎لا يوجد قنوات في الوقت الحالي .. قم يتجميع النقاط بطريقه مختلفه**') != -1:
            await zedub.send_message(event.chat_id, "**⎉╎مـافي قنـوات بالبـوت حاليـاً ...**")
            break
        if con == "ايقاف":
            await zedub.send_message(event.chat_id, "**⎉╎تم إيقـاف تجميـع النقـاط .. بنجـاح☑️**")
            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await zedub(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await zedub(ImportChatInviteRequest(bott))
            msg2 = await zedub.get_messages('@MARKTEBOT', limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**⎉╎تم الاشتـراك في القنـاة  {chs} ...✓**")
        except:
            msg2 = await zedub.get_messages('@MARKTEBOT', limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**⎉╎القنـاة رقـم {chs} .. يمكـن تبنـدت**")
    await zedub.send_message(event.chat_id, "**⎉╎تم الانتهـاء مـن تجميـع النقـاط .. حاول من جديد في وقت آخر ✓**")

@zedub.zed_cmd(pattern="بوت العقاب$")
async def _(event):
    await event.edit('@MARKTEBOT')

# Copyright (C) 2022 Mido . All Rights Reserved
@zedub.zed_cmd(pattern="(العقاب|تجميع العقاب)(?: |$)(.*)")
async def _(event):
    con = event.pattern_match.group(1).lower()
    await event.edit("**⎉╎حسنـاً .. تأكـد من انك مشتـرك بـ قنـوات الاشتـراك الاجبـاري لتجنب الأخطـاء @MARKTEBOT**")
    channel_entity = await zedub.get_entity('@MARKTEBOT')
    await zedub.send_message('@MARKTEBOT', '/start')
    await asyncio.sleep(4)
    msg0 = await zedub.get_messages('@MARKTEBOT', limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await zedub.get_messages('@MARKTEBOT', limit=1)
    await msg1[0].click(0)
    chs = 1
    for i in range(100):
        await asyncio.sleep(10)
        list = await zedub(GetHistoryRequest(peer=channel_entity, limit=1, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('**⎉╎لا يوجد قنوات في الوقت الحالي .. قم يتجميع النقاط بطريقه مختلفه**') != -1:
            await zedub.send_message(event.chat_id, "**⎉╎مـافي قنـوات بالبـوت حاليـاً ...**")
            break
        if con == "ايقاف":
            await zedub.send_message(event.chat_id, "**⎉╎تم إيقـاف تجميـع النقـاط .. بنجـاح☑️**")
            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await zedub(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await zedub(ImportChatInviteRequest(bott))
            msg2 = await zedub.get_messages('@MARKTEBOT', limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**⎉╎تم الاشتـراك في القنـاة  {chs} ...✓**")
        except:
            msg2 = await zedub.get_messages('@MARKTEBOT', limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**⎉╎القنـاة رقـم {chs} .. يمكـن تبنـدت**")
    await zedub.send_message(event.chat_id, "**⎉╎تم الانتهـاء مـن تجميـع النقـاط .. حاول من جديد في وقت آخر ✓**")

@zedub.zed_cmd(pattern="بوت المليون$")
async def _(event):
    await event.edit('@qweqwe1919bot')

# Copyright (C) 2022 Mido . All Rights Reserved
@zedub.zed_cmd(pattern="(المليون|تجميع المليون)(?: |$)(.*)")
async def _(event):
    con = event.pattern_match.group(1).lower()
    await event.edit("**⎉╎حسنـاً .. تأكـد من انك مشتـرك بـ قنـوات الاشتـراك الاجبـاري لتجنب الأخطـاء @qweqwe1919bot**")
    channel_entity = await zedub.get_entity('@qweqwe1919bot')
    await zedub.send_message('@qweqwe1919bot', '/start')
    await asyncio.sleep(4)
    msg0 = await zedub.get_messages('@qweqwe1919bot', limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await zedub.get_messages('@qweqwe1919bot', limit=1)
    await msg1[0].click(0)
    chs = 1
    for i in range(100):
        await asyncio.sleep(10)
        list = await zedub(GetHistoryRequest(peer=channel_entity, limit=1, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('**⎉╎لا يوجد قنوات في الوقت الحالي .. قم يتجميع النقاط بطريقه مختلفه**') != -1:
            await zedub.send_message(event.chat_id, "**⎉╎مـافي قنـوات بالبـوت حاليـاً ...**")
            break
        if con == "ايقاف":
            await zedub.send_message(event.chat_id, "**⎉╎تم إيقـاف تجميـع النقـاط .. بنجـاح☑️**")
            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await zedub(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await zedub(ImportChatInviteRequest(bott))
            msg2 = await zedub.get_messages('@qweqwe1919bot', limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**⎉╎تم الاشتـراك في القنـاة  {chs} ...✓**")
        except:
            msg2 = await zedub.get_messages('@qweqwe1919bot', limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**⎉╎القنـاة رقـم {chs} .. يمكـن تبنـدت**")
    await zedub.send_message(event.chat_id, "**⎉╎تم الانتهـاء مـن تجميـع النقـاط .. حاول من جديد في وقت آخر ✓**")

@zedub.zed_cmd(pattern="بوت سمسم$")
async def _(event):
    await event.edit('@SMSMWAbot')

# Copyright (C) 2023 Mido . All Rights Reserved
@zedub.zed_cmd(pattern="(سمسم|تجميع سمسم)(?: |$)(.*)")
async def _(event):
    con = event.pattern_match.group(1).lower()
    await event.edit("**⎉╎حسنـاً .. تأكـد من انك مشتـرك بـ قنـوات الاشتـراك الاجبـاري لتجنب الأخطـاء @SMSMWAbot**")
    channel_entity = await zedub.get_entity('@SMSMWAbot')
    await zedub.send_message('@SMSMWAbot', '/start')
    await asyncio.sleep(4)
    msgz = await zedub.get_messages('@SMSMWAbot', limit=1)
    await msgz[0].click(0)
    await asyncio.sleep(4)
    msg0 = await zedub.get_messages('@SMSMWAbot', limit=1)
    await msg0[0].click(3)
    await asyncio.sleep(4)
    msg1 = await zedub.get_messages('@SMSMWAbot', limit=1)
    await msg1[0].click(1)
    chs = 1
    for i in range(100):
        await asyncio.sleep(10)
        list = await zedub(GetHistoryRequest(peer=channel_entity, limit=1, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('**⎉╎لا يوجد قنوات في الوقت الحالي .. قم يتجميع النقاط بطريقه مختلفه**') != -1:
            await zedub.send_message(event.chat_id, "**⎉╎مـافي قنـوات بالبـوت حاليـاً ...**")
            break
        if con == "ايقاف":
            await zedub.send_message(event.chat_id, "**⎉╎تم إيقـاف تجميـع النقـاط .. بنجـاح☑️**")
            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await zedub(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await zedub(ImportChatInviteRequest(bott))
            msg2 = await zedub.get_messages('@SMSMWAbot', limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**⎉╎تم الاشتـراك في القنـاة  {chs} ...✓**")
        except:
            msg2 = await zedub.get_messages('@SMSMWAbot', limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**⎉╎القنـاة رقـم {chs} .. يمكـن تبنـدت**")
    await zedub.send_message(event.chat_id, "**⎉╎تم الانتهـاء مـن تجميـع النقـاط .. حاول من جديد في وقت آخر ✓**")

@zedub.zed_cmd(pattern="بوت تناهيد$")
async def _(event):
    await event.edit('@Ncoe_bot')

# Copyright (C) 2023 Mido . All Rights Reserved
@zedub.zed_cmd(pattern="(تناهيد|تجميع تناهيد)(?: |$)(.*)")
async def _(event):
    con = event.pattern_match.group(1).lower()
    await event.edit("**⎉╎حسنـاً .. تأكـد من انك مشتـرك بـ قنـوات الاشتـراك الاجبـاري لتجنب الأخطـاء @Ncoe_bot**")
    channel_entity = await zedub.get_entity('@Ncoe_bot')
    await zedub.send_message('@Ncoe_bot', '/start')
    await asyncio.sleep(4)
    msg0 = await zedub.get_messages('@Ncoe_bot', limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await zedub.get_messages('@Ncoe_bot', limit=1)
    await msg1[0].click(0)
    chs = 1
    for i in range(100):
        await asyncio.sleep(10)
        list = await zedub(GetHistoryRequest(peer=channel_entity, limit=1, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('**⎉╎لا يوجد قنوات في الوقت الحالي .. قم يتجميع النقاط بطريقه مختلفه**') != -1:
            await zedub.send_message(event.chat_id, "**⎉╎مـافي قنـوات بالبـوت حاليـاً ...**")
            break
        if con == "ايقاف":
            await zedub.send_message(event.chat_id, "**⎉╎تم إيقـاف تجميـع النقـاط .. بنجـاح☑️**")
            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await zedub(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await zedub(ImportChatInviteRequest(bott))
            msg2 = await zedub.get_messages('@Ncoe_bot', limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**⎉╎تم الاشتـراك في القنـاة  {chs} ...✓**")
        except:
            msg2 = await zedub.get_messages('@Ncoe_bot', limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**⎉╎القنـاة رقـم {chs} .. يمكـن تبنـدت**")
    await zedub.send_message(event.chat_id, "**⎉╎تم الانتهـاء مـن تجميـع النقـاط .. حاول من جديد في وقت آخر ✓**")

@zedub.zed_cmd(pattern="بوت دعمكم$")
async def _(event):
    await event.edit('@DamKombot')

# Copyright (C) 20223 Mido . All Rights Reserved
@zedub.zed_cmd(pattern="(دعمكم|تجميع دعمكم)(?: |$)(.*)")
async def _(event):
    con = event.pattern_match.group(1).lower()
    await event.edit("**⎉╎حسنـاً .. تأكـد من انك مشتـرك بـ قنـوات الاشتـراك الاجبـاري لتجنب الأخطـاء @DamKombot**")
    channel_entity = await zedub.get_entity('@DamKombot')
    await zedub.send_message('@DamKombot', '/start')
    await asyncio.sleep(4)
    msg0 = await zedub.get_messages('@DamKombot', limit=1)
    await msg0[0].click(1)
    await asyncio.sleep(4)
    msg1 = await zedub.get_messages('@DamKombot', limit=1)
    await msg1[0].click(0)
    chs = 1
    for i in range(100):
        await asyncio.sleep(10)
        list = await zedub(GetHistoryRequest(peer=channel_entity, limit=1, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('**⎉╎لا يوجد قنوات في الوقت الحالي .. قم يتجميع النقاط بطريقه مختلفه**') != -1:
            await zedub.send_message(event.chat_id, "**⎉╎مـافي قنـوات بالبـوت حاليـاً ...**")
            break
        if con == "ايقاف":
            await zedub.send_message(event.chat_id, "**⎉╎تم إيقـاف تجميـع النقـاط .. بنجـاح☑️**")
            break
        msg_text = msgs.message
        if "اشترك فالقناة @" in msg_text:
            the_channel = msg_text.split('@')[1].split()[0]
            try:
                entity = await zedub.get_entity(the_channel)
                if entity:
                    await zedub(JoinChannelRequest(entity.id))
                    await asyncio.sleep(4)
                    msg2 = await zedub.get_messages('@DamKombot', limit=1)
                    await msg2[0].click(text='اشتركت ✅')
                    chs += 1
                    await event.edit(f"**⎉╎تم الاشتـراك في القنـاة  {chs} ...✓**")
            except:
                await zedub.send_message(event.chat_id, f"**⎉╎خطـأ , يمكـن تبنـدت ؟!**")
                break
    await zedub.send_message(event.chat_id, "**⎉╎تم الانتهـاء مـن تجميـع النقـاط .. حاول من جديد في وقت آخر ✓**")

# Code by @r0r77 & @Dar4k
@zedub.zed_cmd(pattern=r"بخشيش وعد(?:\s|$)([\s\S]*)")
async def baqshis(event):
    global bahsees
    await event.delete()
    if not bahsees:
        bahsees = True
        if event.is_group:
            await the_bahsees(event)
        else:
            await event.edit("**⎉╎ الامـر خاص بـ المجموعات فقـط ؟!**")
async def the_bahsees(event):
    await event.respond('بخشيش')
    await asyncio.sleep(660)
    global bahsees
    if bahsees:
        await the_bahsees(event)
@zedub.zed_cmd(pattern=r"ايقاف بخشيش وعد(?:\s|$)([\s\S]*)")
async def baqshis(event):
    global bahsees
    bahsees = False
    await event.edit("**⎉╎تم إيقـاف تجميـع البخشيش  .. بنجـاح ✓** ")

@zedub.zed_cmd(pattern=r"سرقة وعد(?:\s|$)([\s\S]*)")
async def thift(event):
    global thifts
    await event.delete()
    if not thifts:
        thifts = True
        if event.is_group:
            message = event.pattern_match.group(1).strip()
            if message:
                await send_message(event, message)
            else:
                await event.edit("**⎉╎قم بكتابة ايدي الشخص مع الامـر ؟!**")

async def send_message(event, message):
    await event.respond(f"زرف {message}")
    await asyncio.sleep(660)
    global thifts
    if thifts:
        await send_message(event, message)

@zedub.zed_cmd(pattern=r"ايقاف سرقة وعد(?:\s|$)([\s\S]*)")
async def Reda(event):
    global thifts
    thifts = False
    await event.edit("**⎉╎تم إيقـاف السرقة  .. بنجـاح ✓**")
client = zedub

@zedub.zed_cmd(pattern=r"راتب وعد(?:\s|$)([\s\S]*)")
async def thift(event):
    global ratp
    await event.delete()
    if not ratp:
        ratp = True
        if event.is_group:
            await the_ratp(event)
        else:
            await event.edit("**⎉╎ الامـر خاص بـ المجموعات فقـط ؟!**")

async def the_ratp(event):
    await event.respond('راتب')
    await asyncio.sleep(660)
    global ratp
    if ratp:
        await the_ratp(event)
@zedub.zed_cmd(pattern=r"ايقاف راتب وعد(?:\s|$)([\s\S]*)")
async def thift(event):
    global ratp
    ratp = False
    await event.edit("**تم تعطيل راتب وعد بنجاح ✅**")

@zedub.zed_cmd(pattern="كلمات وعد (.*)")
async def waorwaad(event):
    for i in range(int("".join(event.text.split(maxsplit=2)[2:]).split(" ", 2)[0])):
        chat = event.chat_id
        await zedub.send_message(chat, "كلمات")
        await asyncio.sleep(0.5)
        masg = await zedub.get_messages(chat, limit=1)
        masg = masg[0].message
        masg = ("".join(masg.split(maxsplit=3)[3:])).split(" ", 2)
        if len(masg) == 2:
            msg = masg[0]
            await zedub.send_message(chat, msg)
        else:
            msg = masg[0] + " " + masg[1]
            await zedub.send_message(chat, msg)

@zedub.zed_cmd(pattern="استثمار وعد")
async def _(event):
    await event.delete()
    global estithmar
    estithmar = True
    while estithmar:
        if event.is_group:
            await event.client.send_message(event.chat_id, "فلوسي")
            await asyncio.sleep(4)
            zzzthon = await event.client.get_messages(event.chat_id, limit=1)
            zzzthon = zzzthon[0].message
            zzzthon = ("".join(zzzthon.split(maxsplit=2)[2:])).split(" ", 2)
            zedub = zzzthon[0]
            if zedub.isdigit() and int(zedub) > 500000000:
                await event.client.send_message(event.chat_id,f"استثمار {zedub}")
                await asyncio.sleep(5)
                zzthon = await event.client.get_messages(event.chat_id, limit=1)
                await zzthon[0].click(text="اي ✅")
            else:
                await event.client.send_message(event.chat_id, f"استثمار {zedub}")
            await asyncio.sleep(1210)

        else:
            await event.edit("**⎉╎امر الاستثمار يمكنك استعماله في المجموعات فقط 🖤**")
@zedub.zed_cmd(pattern="ايقاف استثمار وعد")
async def stop_wad(event):
    global estithmar
    estithmar = False
    await event.edit("**⎉╎تم إيقـاف استثمار وعـد  .. بنجـاح ✓**")

@zedub.zed_cmd(pattern="اوامر النقاط")
async def cmd(zelzallll):
    await edit_or_reply(zelzallll, ZelzalCoins_cmd)

@zedub.zed_cmd(pattern="اوامر التجميع")
async def cmd(zelzallll):
    await edit_or_reply(zelzallll, ZelzalCoins_cmd)
