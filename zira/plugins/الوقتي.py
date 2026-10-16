# @Mido - Mido
# Copyright (C) 2022 Mido . All Rights Reserved
#
# This file is a part of < https://github.com/Mido/Mido/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/Mido/Mido/blob/master/LICENSE/>.
#كـود الصورة الوقتيه كتـابتي وتعديلـي من زمان ومتعوب عليها
#+ كـود زخـرفة الصورة الوقتيه
#+ دددي لا ابلـع حســابك بـانـد بطـعـم الليمــون 🍋😹🤘
#Mido الهيبــه يـ ولــد - حقــوق لـ التــاريـخ ®
#هههههههههههههههههههههههههههههههههههههههههههههههههه

import asyncio
import math
import os
import shutil
import time
import urllib3
import base64
import requests
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
from pySmartDL import SmartDL
from telegraph import Telegraph, exceptions, upload_file
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from telethon.errors import FloodWaitError
from telethon.tl import functions
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityMentionName

from ..Config import Config
from ..helpers.utils import _format
from ..core.managers import edit_or_reply
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from . import edit_delete, zedub, logging, BOTLOG_CHATID, mention

plugin_category = "الادوات"
DEFAULTUSER = gvarstatus("ALIVE_NAME") or Config.ALIVE_NAME
LOGS = logging.getLogger(__name__)
CHANGE_TIME = int(gvarstatus("CHANGE_TIME")) if gvarstatus("CHANGE_TIME") else 60
FONT_FILE_TO_USE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

normzltext = "1234567890"

autopic_path = os.path.join(os.getcwd(), "zira", "original_pic.png")
digitalpic_path = os.path.join(os.getcwd(), "zira", "digital_pic.png")
autophoto_path = os.path.join(os.getcwd(), "zira", "photo_pfp.png")

NAUTO = gvarstatus("Z_NAUTO") or "(الاسم تلقائي|الاسم الوقتي|اسم وقتي|اسم تلقائي)"
PAUTO = gvarstatus("Z_PAUTO") or "(البروفايل تلقائي|الصوره الوقتيه|الصورة الوقتية|صوره وقتيه|البروفايل)"
BAUTO = gvarstatus("Z_BAUTO") or "(البايو تلقائي|البايو الوقتي|بايو وقتي|نبذه وقتيه|النبذه الوقتيه)"

async def digitalpicloop():
    DIGITALPICSTART = gvarstatus("digitalpic") == "true"
    i = 0
    while DIGITALPICSTART:
        if not os.path.exists(digitalpic_path):
            digitalpfp = gvarstatus("DIGITAL_PIC")
            downloader = SmartDL(digitalpfp, digitalpic_path, progress_bar=False)
            downloader.start(blocking=False)
            while not downloader.isFinished():
                pass
        zedfont = gvarstatus("DEFAULT_PIC") or "zira/helpers/styles/Papernotes.ttf"
        shutil.copy(digitalpic_path, autophoto_path)
        Image.open(autophoto_path)
        current_time = datetime.now().strftime("%I:%M")
        img = Image.open(autophoto_path)
        drawn_text = ImageDraw.Draw(img)
        fnt = ImageFont.truetype(f"{zedfont}", 35)
        drawn_text.text((140, 70), current_time, font=fnt, fill=(280, 280, 280))
        img.save(autophoto_path)
        file = await zedub.upload_file(autophoto_path)
        try:
            if i > 0:
                await zedub(
                    functions.photos.DeletePhotosRequest(
                        await zedub.get_profile_photos("me", limit=1)
                    )
                )
            i += 1
            await zedub(functions.photos.UploadProfilePhotoRequest(file))
            os.remove(autophoto_path)
            await asyncio.sleep(CHANGE_TIME)
        except BaseException:
            return
        DIGITALPICSTART = gvarstatus("digitalpic") == "true"

async def autoname_loop():
    while AUTONAMESTART := gvarstatus("autoname") == "true":
        DM = time.strftime("%d-%m-%y")
        HM = time.strftime("%I:%M")
        for normal in HM:
            if normal in normzltext:
              namerzfont = gvarstatus("ZI_FN") or "𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝟬"
              namefont = namerzfont[normzltext.index(normal)]
              HM = HM.replace(normal, namefont)
        ZEDT = gvarstatus("CUSTOM_ALIVE_EMZED") or " 𓏺"
        name = f"{HM}{ZEDT}"
        LOGS.info(name)
        try:
            await zedub(functions.account.UpdateProfileRequest(first_name=name))
        except FloodWaitError as ex:
            LOGS.warning(str(ex))
            await asyncio.sleep(ex.seconds)
        await asyncio.sleep(CHANGE_TIME)
        AUTONAMESTART = gvarstatus("autoname") == "true"

async def autobio_loop():
    AUTOBIOSTART = gvarstatus("autobio") == "true"
    while AUTOBIOSTART:
        DMY = time.strftime("%d.%m.%Y")
        HM = time.strftime("%I:%M")
        for normal in HM:
            if normal in normzltext:
              namerzfont = gvarstatus("ZI_FN") or "𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝟬"
              namefont = namerzfont[normzltext.index(normal)]
              HM = HM.replace(normal, namefont)
        DEFAULTUSERBIO = gvarstatus("DEFAULT_BIO") or "‏{وَتَوَكَّلْ عَلَى اللَّهِ ۚ وَكَفَىٰ بِاللَّهِ وَكِيلًا}"
        bio = f"{DEFAULTUSERBIO} ⏐ {HM}"
        LOGS.info(bio)
        try:
            await zedub(functions.account.UpdateProfileRequest(about=bio))
        except FloodWaitError as ex:
            LOGS.warning(str(ex))
            await asyncio.sleep(ex.seconds)
        await asyncio.sleep(CHANGE_TIME)
        AUTOBIOSTART = gvarstatus("autobio") == "true"

@zedub.zed_cmd(pattern=f"{PAUTO}$")
async def _(event):
    digitalpfp = gvarstatus("DIGITAL_PIC")
    downloader = SmartDL(digitalpfp, digitalpic_path, progress_bar=False)
    downloader.start(blocking=False)
    while not downloader.isFinished():
        pass
    if gvarstatus("DIGITAL_PIC") is None:
        return await edit_delete(event, "**- فار الصـورة الوقتيـه غيـر موجـود ؟!**\n**- ارسـل صورة ثم قم بالـرد عليهـا بالامـر :**\n\n`.اضف صورة الوقتي`")
    if gvarstatus("digitalpic") is not None and gvarstatus("digitalpic") == "true":
        return await edit_delete(event, "**⎉╎البروفـايل الوقتـي .. تم تفعيلهـا سابقـاً**")
    addgvar("digitalpic", True)
    await edit_delete(event, "**⎉╎تـم بـدء البروفـايل الوقتـي .. بنجـاح ✓**")
    await digitalpicloop()

@zedub.zed_cmd(pattern=f"{NAUTO}$")
async def _(event):
    if gvarstatus("autoname") is not None and gvarstatus("autoname") == "true":
        return await edit_delete(event, "**⎉╎الاسـم الوقتـي .. تم تفعيلـه سابقـاً**")
    addgvar("autoname", True)
    await edit_delete(event, "**⎉╎تـم بـدء الاسـم الوقتـي .. بنجـاح ✓**")
    await autoname_loop()

@zedub.zed_cmd(pattern=f"{BAUTO}$")
async def _(event):
    if gvarstatus("DEFAULT_BIO") is None:
        return await edit_delete(event, "**- فار النبـذة الوقتيـه غيـر موجـود ؟!**\n**- ارسـل نـص النبـذه ثم قم بالـرد عليهـا بالامـر :**\n\n`.اضف البايو`")
    if gvarstatus("autobio") is not None and gvarstatus("autobio") == "true":
        return await edit_delete(event, "**⎉╎النبـذه الوقتـيه .. مفعلـه سابقـاً**")
    addgvar("autobio", True)
    await edit_delete(event, "**⎉╎تـم بـدء الـنبذة الوقتيـه .. بنجـاح ✓**")
    await autobio_loop()

@zedub.zed_cmd(
    pattern=r"الغاء ([\s\S]*)",
    command=("الغاء", plugin_category),
    info={
        "header": "To stop the functions of autoprofile",
        "description": "If you want to stop autoprofile functions then use this cmd.",
        "options": {
            "digitalpfp": "To stop difitalpfp",
            "autoname": "To stop autoname",
            "autobio": "To stop autobio",
        },
        "usage": "{tr}end <option>",
        "examples": ["{tr}end autopic"],
    },
)
async def _(event):  # sourcery no-metrics
    "To stop the functions of autoprofile plugin"
    input_str = event.pattern_match.group(1)
    if input_str == "البروفايل تلقائي" or input_str == "البروفايل" or input_str == "البروفايل التلقائي" or input_str == "الصوره الوقتيه" or input_str == "الصورة الوقتية":
        if gvarstatus("digitalpic") is not None and gvarstatus("digitalpic") == "true":
            delgvar("digitalpic")
            await event.client(
                functions.photos.DeletePhotosRequest(
                    await event.client.get_profile_photos("me", limit=1)
                )
            )
            return await edit_delete(event, "**⎉╎تم إيقـاف البروفـايل الوقتـي .. بنجـاح ✓**")
        return await edit_delete(event, "**⎉╎البروفـايل الوقتـي .. غيـر مفعـل اصـلاً ؟!**")
    if input_str == "الاسم تلقائي" or input_str == "الاسم" or input_str == "الاسم التلقائي" or input_str == "الاسم الوقتي" or input_str == "اسم الوقتي":
        if gvarstatus("autoname") is not None and gvarstatus("autoname") == "true":
            delgvar("autoname")
            await event.client(
                functions.account.UpdateProfileRequest(first_name=DEFAULTUSER)
            )
            return await edit_delete(event, "**⎉╎تم إيقـاف الاسـم الوقتـي .. بنجـاح ✓**")
        return await edit_delete(event, "**⎉╎الاسـم الوقتـي .. غيـر مفعـل اصـلاً ؟!**")
    if input_str == "البايو تلقائي" or input_str == "البايو" or input_str == "البايو التلقائي" or input_str == "البايو الوقتي" or input_str == "النبذه الوقتيه" or input_str == "النبذة الوقتية" or input_str == "بايو الوقتي" or input_str == "نبذه الوقتي":
        if gvarstatus("autobio") is not None and gvarstatus("autobio") == "true":
            delgvar("autobio")
            DEFAULTUSERBIO = gvarstatus("DEFAULT_BIO") or "الحمد الله على كل شئ - @Mido"
            await event.client(
                functions.account.UpdateProfileRequest(about=DEFAULTUSERBIO)
            )
            return await edit_delete(event, "**⎉╎تم إيقـاف النبـذه الوقتيـه .. بنجـاح ✓**")
        return await edit_delete(event, "**⎉╎النبـذه الوقتيـه .. غيـر مفعـله اصـلاً ؟!**")

@zedub.zed_cmd(
    pattern=r"ايقاف ([\s\S]*)",
    command=("ايقاف", plugin_category),
    info={
        "header": "To stop the functions of autoprofile",
        "description": "If you want to stop autoprofile functions then use this cmd.",
        "options": {
            "digitalpfp": "To stop difitalpfp",
            "autoname": "To stop autoname",
            "autobio": "To stop autobio",
        },
        "usage": "{tr}end <option>",
        "examples": ["{tr}end autopic"],
    },
)
async def _(event):  # sourcery no-metrics
    "To stop the functions of autoprofile plugin"
    input_str = event.pattern_match.group(1)
    if input_str == "البروفايل تلقائي" or input_str == "البروفايل" or input_str == "البروفايل التلقائي" or input_str == "الصوره الوقتيه" or input_str == "الصورة الوقتية":
        if gvarstatus("digitalpic") is not None and gvarstatus("digitalpic") == "true":
            delgvar("digitalpic")
            await event.client(
                functions.photos.DeletePhotosRequest(
                    await event.client.get_profile_photos("me", limit=1)
                )
            )
            return await edit_delete(event, "**⎉╎تم إيقـاف البروفـايل الوقتـي .. بنجـاح ✓**")
        return await edit_delete(event, "**⎉╎البروفـايل الوقتـي .. غيـر مفعـل اصـلاً ؟!**")
    if input_str == "الاسم تلقائي" or input_str == "الاسم" or input_str == "الاسم التلقائي" or input_str == "الاسم الوقتي" or input_str == "اسم الوقتي" or input_str == "اسم وقتي" or input_str == "اسم تلقائي":
        if gvarstatus("autoname") is not None and gvarstatus("autoname") == "true":
            delgvar("autoname")
            await event.client(
                functions.account.UpdateProfileRequest(first_name=DEFAULTUSER)
            )
            return await edit_delete(event, "**⎉╎تم إيقـاف الاسـم الوقتـي .. بنجـاح ✓**")
        return await edit_delete(event, "**⎉╎الاسـم الوقتـي .. غيـر مفعـل اصـلاً ؟!**")
    if input_str == "البايو تلقائي" or input_str == "البايو" or input_str == "البايو التلقائي" or input_str == "البايو الوقتي" or input_str == "النبذه الوقتيه" or input_str == "النبذة الوقتية" or input_str == "بايو الوقتي" or input_str == "نبذه الوقتي":
        if gvarstatus("autobio") is not None and gvarstatus("autobio") == "true":
            delgvar("autobio")
            DEFAULTUSERBIO = gvarstatus("DEFAULT_BIO") or "الحمد الله على كل شئ - @Mido"
            await event.client(
                functions.account.UpdateProfileRequest(about=DEFAULTUSERBIO)
            )
            return await edit_delete(event, "**⎉╎تم إيقـاف النبـذه الوقتيـه .. بنجـاح ✓**")
        return await edit_delete(event, "**⎉╎النبـذه الوقتيـه .. غيـر مفعـله اصـلاً ؟!**")

@zedub.zed_cmd(
    pattern=r"انهاء ([\s\S]*)",
    command=("انهاء", plugin_category),
    info={
        "header": "To stop the functions of autoprofile",
        "description": "If you want to stop autoprofile functions then use this cmd.",
        "options": {
            "digitalpfp": "To stop difitalpfp",
            "autoname": "To stop autoname",
            "autobio": "To stop autobio",
        },
        "usage": "{tr}end <option>",
        "examples": ["{tr}end autopic"],
    },
)
async def _(event):  # sourcery no-metrics
    "To stop the functions of autoprofile plugin"
    input_str = event.pattern_match.group(1)
    if input_str == "البروفايل تلقائي" or input_str == "البروفايل" or input_str == "البروفايل التلقائي" or input_str == "الصوره الوقتيه" or input_str == "الصورة الوقتية":
        if gvarstatus("digitalpic") is not None and gvarstatus("digitalpic") == "true":
            delgvar("digitalpic")
            await event.client(
                functions.photos.DeletePhotosRequest(
                    await event.client.get_profile_photos("me", limit=1)
                )
            )
            return await edit_delete(event, "**⎉╎تم إيقـاف البروفـايل الوقتـي .. بنجـاح ✓**")
        return await edit_delete(event, "**⎉╎البروفـايل الوقتـي .. غيـر مفعـل اصـلاً ؟!**")
    if input_str == "الاسم تلقائي" or input_str == "الاسم" or input_str == "الاسم التلقائي" or input_str == "الاسم الوقتي" or input_str == "اسم الوقتي" or input_str == "اسم وقتي" or input_str == "اسم تلقائي":
        if gvarstatus("autoname") is not None and gvarstatus("autoname") == "true":
            delgvar("autoname")
            await event.client(
                functions.account.UpdateProfileRequest(first_name=DEFAULTUSER)
            )
            return await edit_delete(event, "**⎉╎تم إيقـاف الاسـم الوقتـي .. بنجـاح ✓**")
        return await edit_delete(event, "**⎉╎الاسـم الوقتـي .. غيـر مفعـل اصـلاً ؟!**")
    if input_str == "البايو تلقائي" or input_str == "البايو" or input_str == "البايو التلقائي" or input_str == "البايو الوقتي" or input_str == "النبذه الوقتيه" or input_str == "النبذة الوقتية" or input_str == "بايو الوقتي" or input_str == "نبذه الوقتي":
        if gvarstatus("autobio") is not None and gvarstatus("autobio") == "true":
            delgvar("autobio")
            DEFAULTUSERBIO = gvarstatus("DEFAULT_BIO") or "الحمد الله على كل شئ - @Mido"
            await event.client(
                functions.account.UpdateProfileRequest(about=DEFAULTUSERBIO)
            )
            return await edit_delete(event, "**⎉╎تم إيقـاف النبـذه الوقتيـه .. بنجـاح ✓**")
        return await edit_delete(event, "**⎉╎النبـذه الوقتيـه .. غيـر مفعـله اصـلاً ؟!**")
    END_CMDS = [
        "البروفايل تلقائي",
        "الصوره الوقتيه",
        "الاسم تلقائي",
        "الاسم الوقتي",
        "اسم تلقائي",
        "اسم وقتي",
        "البايو تلقائي",
        "البايو الوقتي",
        "النبذه الوقتيه",
        "البروفايل",
        "الاسم",
        "البايو",
    ]
    if input_str not in END_CMDS:
        await edit_delete(
            event,
            f"{input_str} is invalid end command.Mention clearly what should i end.",
            parse_mode=_format.parse_pre,
        )

zedub.loop.create_task(digitalpicloop())
zedub.loop.create_task(autoname_loop())
zedub.loop.create_task(autobio_loop())

# ================================================================================================ #
# =========================================الوقتيه================================================= #
# ================================================================================================ #
# Mido
# Copyright (C) 2022 Mido . All Rights Reserved
#
# This file is a part of < https://github.com/Mido/Mido/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/Mido/Mido/blob/master/LICENSE/>.

""" وصـف الملـف : اوامـر تغييـر زخـارف البروفايـل والاسـم الوقـتي باللغـة العربيـة كـاملة ولا حـرف انكلـش🤘 تخمـط اذكـر المصـدر يولـد
زخـارف ممطـروقـه بـ امـر واحـد فقـط
حقـوق للتـاريخ : @Mido
@M_O_EG - كتـابـة الملـف :  Mido الهيبــه"""
#Mido يولـد هههههههههههههههههههههههههه

telegraph = Telegraph()
r = telegraph.create_account(short_name=Config.TELEGRAPH_SHORT_NAME)
auth_url = r["auth_url"]

ZelzalVP_cmd = (
    "𓆩 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - اوامـر الفـارات 𓆪\n\n"
    "**✾╎قائـمه اوامـر تغييـر زخـارف البروفايـل + الاسـم الوقـتي بأمـر واحـد فقـط - حقـوق لـ التـاريـخ 🦾 :** \n\n"
    "⪼ `.وقتيه 1` / `.الوقتي 1`\n\n"
    "⪼ `.وقتيه 2` / `.الوقتي 2`\n\n"
    "⪼ `.وقتيه 3` / `.الوقتي 3`\n\n"
    "⪼ `.وقتيه 4` / `.الوقتي 4`\n\n"
    "⪼ `.وقتيه 5` / `.الوقتي 5`\n\n"
    "⪼ `.وقتيه 6` / `.الوقتي 6`\n\n"
    "⪼ `.وقتيه 7` / `.الوقتي 7`\n\n"
    "⪼ `.وقتيه 8` / `.الوقتي 8`\n\n"
    "⪼ `.وقتيه 9` / `.الوقتي 9`\n\n"
    "⪼ `.وقتيه 10` / `.الوقتي 10`\n\n"
    "⪼ `.وقتيه 11` / `.الوقتي 11`\n\n"
    "⪼ `.وقتيه 12` / `.الوقتي 12`\n\n"
    "⪼ `.وقتيه 13` / `.الوقتي 13`\n\n"
    "⪼ `.وقتيه 14` / `.الوقتي 14`\n\n"
    "⪼ `.وقتيه 15`\n\n"
    "⪼ `.وقتيه 16`\n\n"
    "⪼ `.وقتيه 17`\n\n\n"
    "**✾╎لـ رؤيـة زغـارف البروفايـل الوقتـي ↶**  ⦇  اضـغـط هنــا  ⦈ \n\n"
    "**✾╎لـ رؤيـة زغـارف الاســم الوقتـي ↶**  ⦇  اضـغـط هنــا  ⦈ \n\n\n"
    "🛃 سيتـم اضـافة المزيـد من الزغـارف بالتحديثـات الجـايـه\n\n"
    "\n𓆩 𐇮 Mido الهہـيـٖ͡ـ͢ـبـه 𐇮 𓆪"
)

# Copyright (C) 2022 @Mido . All Rights Reserved
@zedub.zed_cmd(pattern=r"وقتيه(?:\s|$)([\s\S]*)")
async def variable(event):
    input_str = event.pattern_match.group(1)
    zed = await edit_or_reply(event, "**✾╎جـاري اضـافة زخـرفـة الوقتيـه لـ بوتـك 💞🦾 . . .**")
    # All Rights Reserved for "@Mido" "Mido الهيبـه"
    if input_str == "1":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Mido.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "2":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Starjedi.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "3":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Papernotes.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "4":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Terserah.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "5":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Photography Signature.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "6":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Austein.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "7":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Dream MMA.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "8":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/EASPORTS15.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "9":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/KGMissKindergarten.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "10":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/212 Orion Sans PERSONAL USE.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "11":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/PEPSI_pl.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "12":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Paskowy.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "13":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Cream Cake.otf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "14":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Hello Valentina.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "15":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Alien-Encounters-Regular.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "16":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/Linebeam.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "17":
        variable = "DEFAULT_PIC"
        zinfo = "zira/helpers/styles/EASPORTS15.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("DEFAULT_PIC") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة البروفـايل الوقـتي {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.البروفايل` **لـ بـدء البروفـايل الوقتـي . .**".format(input_str))
        addgvar(variable, zinfo)

# Copyright (C) 2022 @Mido . All Rights Reserved
@zedub.zed_cmd(pattern=r"الوقتي(?:\s|$)([\s\S]*)")
async def hhhzelzal(event):
    input_str = event.pattern_match.group(1)
    zed = await edit_or_reply(event, "**✾╎جـاري اضـافة زخـرفـة الوقتيـه لـ بوتـك 💞🦾 . . .**")
    # All Rights Reserved for "@Mido" "Mido الهيبـه"
    if input_str == "1":
        zinfo = "𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝟬"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝟬")
    elif input_str == "2":
        zinfo = "𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗𝟎"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗𝟎")
    elif input_str == "3":
        zinfo = "١٢٣٤٥٦٧٨٩٠"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "١٢٣٤٥٦٧٨٩٠")
    elif input_str == "4":
        zinfo = "₁₂₃₄₅₆₇₈₉₀"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "₁₂₃₄₅₆₇₈₉₀")
    elif input_str == "5":
        zinfo = "¹²³⁴⁵⁶⁷⁸⁹⁰"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "¹²³⁴⁵⁶⁷⁸⁹⁰")
    elif input_str == "6":
        zinfo = "➊➋➌➍➎➏➐➑➒✪"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "➊➋➌➍➎➏➐➑➒✪")
    elif input_str == "7":
        zinfo = "❶❷❸❹❺❻❼❽❾⓿"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "❶❷❸❹❺❻❼❽❾⓿")
    elif input_str == "8":
        zinfo = "➀➁➂➃➄➅➆➇➈⊙"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "➀➁➂➃➄➅➆➇➈⊙")
    elif input_str == "9":
        zinfo = "⓵⓶⓷⓸⓹⓺⓻⓼⓽⓪"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "⓵⓶⓷⓸⓹⓺⓻⓼⓽⓪")
    elif input_str == "10":
        zinfo = "①②③④⑤⑥⑦⑧⑨⓪"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "①②③④⑤⑥⑦⑧⑨⓪")
    elif input_str == "11":
        zinfo = "𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫𝟢"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫𝟢")
    elif input_str == "12":
        zinfo = "𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿𝟶"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿𝟶")
    elif input_str == "13":
        zinfo = "𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡𝟘"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡𝟘")
    elif input_str == "14":
        zinfo = "１２３４５６７８９０"
        await asyncio.sleep(1.5)
        if gvarstatus("ZI_FN") is not None:
            await zed.edit("**✾╎تم تغييـر زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎الان ارسـل ↶** `.الاسم تلقائي`".format(zinfo))
        else:
            await zed.edit("**✾╎تم إضـافة زغـرفة الاسـم الوقتـي .. بنجـاح✓**\n**✾╎نـوع الزخـرفـه {} **\n**✾╎ارسـل الان ↶** `.الاسم تلقائي`".format(zinfo))
        addgvar("ZI_FN", "１２３４５６７８９０")

# Copyright (C) 2022 @Mido . All Rights Reserved
@zedub.zed_cmd(pattern="اوامر الوقتي")
async def cmd(zelzallll):
    await edit_or_reply(zelzallll, ZelzalVP_cmd)

# Copyright (C) 2022 @Mido . All Rights Reserved
@zedub.zed_cmd(pattern=r"الخط(?:\s|$)([\s\S]*)")
async def variable(event):
    input_str = event.pattern_match.group(1)
    zed = await edit_or_reply(event, "**✾╎جـاري اضـافة زخـرفـة خـط الحقـوق لـ بوتـك 💞🦾 . . .**")
    # All Rights Reserved for "@Mido" "Mido الهيبـه"
    if input_str == "1":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Mido.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "2":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Starjedi.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "3":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Papernotes.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "4":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Terserah.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "5":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Photography Signature.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "6":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Austein.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "7":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Dream MMA.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "8":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/EASPORTS15.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "9":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/KGMissKindergarten.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "10":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/212 Orion Sans PERSONAL USE.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "11":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/PEPSI_pl.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "12":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Paskowy.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "13":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Cream Cake.otf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "14":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Hello Valentina.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "15":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Alien-Encounters-Regular.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "16":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/Linebeam.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
    elif input_str == "17":
        variable = "ZED_FONTS"
        zinfo = "zira/helpers/styles/EASPORTS15.ttf"
        await asyncio.sleep(1.5)
        if gvarstatus("ZED_FONTS") is None:
            await zed.edit("**✾╎تم اضـافـة زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        else:
            await zed.edit("**✾╎تم تغييـر زغـرفـة خـط الحقـوق {} بنجـاح ☑️**\n\n**✾╎الان قـم بـ ارسـال الامـر ↶** `.حقوق` **+ كلمـه بالـرد ع (صوره-ملصق-متحركه-فيديو) . .**".format(input_str))
        addgvar(variable, zinfo)
