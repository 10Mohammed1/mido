import asyncio
import glob
import os

from . import zedub

from ..core.managers import edit_delete, edit_or_reply
from ..helpers.utils import _zedutils
from . import BOTLOG, BOTLOG_CHATID, mention

plugin_category = "الادوات"


# ============================@ Constants @===============================
config = "./config.py"
var_checker = [
    "APP_ID",
    "PM_LOGGER_GROUP_ID",
    "PRIVATE_CHANNEL_BOT_API_ID",
    "PRIVATE_GROUP_BOT_API_ID",
]
exts = ["jpg", "png", "webp", "webm", "m4a", "mp4", "mp3", "tgs"]

cmds = [
    "rm -rf downloads",
    "mkdir downloads",
]
# ========================================================================


@zedub.zed_cmd(
    pattern=r"(ضع|جلب|حذف) الفار ([\s\S]*)",
    command=("الفار", plugin_category),
    info={
        "header": "To manage config vars.",
        "flags": {
            "set": "To set new var in vps or modify the old var",
            "get": "To show the already existing var value.",
            "del": "To delete the existing value",
        },
        "usage": [
            "{tr}ضع الفار <اسم الفار> <قيمة الفار>",
            "{tr}جلب الفار <اسم الفار>",
            "{tr}حذف الفار <اسم الفار>",
        ],
        "examples": [
            "{tr}جلب الفار ALIVE_NAME",
        ],
    },
)
async def variable(event):  # sourcery no-metrics
    """
    Manage most of ConfigVars setting, set new var, get current var, or delete var...
    """
    if not os.path.exists(config):
        return await edit_delete(
            event, "**- عـذراً .. لايـوجـد هنـالك ملـف كـونفـج 📁🖇**\n\n**- هـذه الاوامـر خـاصـة فقـط بالمنصبيـن ع السيـرفـر 📟💡**"
        )
    cmd = event.pattern_match.group(1)
    string = ""
    match = None
    with open(config, "r") as f:
        configs = f.readlines()
    if cmd == "جلب":
        cat = await edit_or_reply(event, "**⌔∮ جاري الحصول على المعلومات. **")
        await asyncio.sleep(1)
        variable = event.pattern_match.group(2).split()[0]
        for i in configs:
            if variable in i:
                _, val = i.split("= ")
                return await cat.edit("𓆩 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - 𝗖𝗼𝗻𝗳𝗶𝗴 𝗩𝗮𝗿𝘀 𓆪\n𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻" f"\n\n**⌔∮الفـار** `{variable} = {val}`")
        await cat.edit(
            "𓆩 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - 𝗖𝗼𝗻𝗳𝗶𝗴 𝗩𝗮𝗿𝘀 𓆪\n𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻" f"\n\n**⌔∮الفـار :** -> {variable} **غيـر موجود**❌"
        )
    elif cmd == "ضع":
        variable = "".join(event.text.split(maxsplit=2)[2:])
        cat = await edit_or_reply(event, "**⌔∮جـارِ إعـداد المعلومـات . . .**")
        if not variable:
            return await cat.edit("**⌔∮** `.ضع الفار ` **<اسـم الفـار> <القيمـه>**")
        value = "".join(variable.split(maxsplit=1)[1:])
        variable = "".join(variable.split(maxsplit=1)[0])
        if variable not in var_checker:
            value = f"'{value}'"
        if not value:
            return await cat.edit("**⌔∮** `.ضع الفار ` **<اسـم الفـار> <القيمـه>**")
        await asyncio.sleep(1)
        for i in configs:
            if variable in i:
                string += f"    {variable} = {value}\n"
                match = True
            else:
                string += f"{i}"
        if match:
            await cat.edit(f"**- تم تغيـر** `{variable}` **:**\n **- المتغيـر :** `{value}` \n**- يتم الان اعـادة تشغيـل بـوت Mido يستغـرق الامر 2-1 دقيقـه ▬▭ ...**")
        else:
            string += f"    {variable} = {value}\n"
            await cat.edit(
                f"**- تم إضـافـة** `{variable}` **:**\n **- المضـاف اليـه :** `{value}` \n**- يتم الان اعـادة تشغيـل بـوت Mido يستغـرق الامر 2-1 دقيقـه ▬▭ ...**"
            )
        with open(config, "w") as f1:
            f1.write(string)
            f1.close()
        await event.client.reload(cat)
    if cmd == "حذف":
        cat = await edit_or_reply(event, "**⌔∮جـارِ الحصول على معلومات لحذف المتغير الفـار من السيـرفـر ...**")
        await asyncio.sleep(1)
        variable = event.pattern_match.group(2).split()[0]
        for i in configs:
            if variable in i:
                match = True
            else:
                string += f"{i}"
        with open(config, "w") as f1:
            f1.write(string)
            f1.close()
        if match:
            await cat.edit(f"**- الفـار** `{variable}`  **تم حذفه بنجاح. \n\n**- يتم الان اعـادة تشغيـل بـوت Mido يستغـرق الامر 2-1 دقيقـه ▬▭ ...**")
        else:
            await cat.edit(
                "𓆩 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - 𝗖𝗼𝗻𝗳𝗶𝗴 𝗩𝗮𝗿𝘀 𓆪\n𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻" f"\n\n**⌔∮الفـار :** -> {variable} **غيـر موجود**❌"
            )
        await event.client.reload(cat)


@zedub.zed_cmd(
    pattern="(ري|كلين) لود$",
    command=("لود", plugin_category),
    info={
        "header": "To reload your bot in vps/ similar to restart",
        "الاوامر المضافه لـ لـود": {
            "ري": "restart your bot without deleting junk files",
            "كلين": "delete all junk files & restart",
        },
        "الاسـتخـدام": [
            "{tr}ري لود",
            "{tr}كلين لود",
        ],
    },
)
async def _(event):
    "لـ اعـادة اشغيـل البـوت في السيـرفـر"
    cmd = event.pattern_match.group(1)
    zed = await edit_or_reply(
        event,
        f"**⌔∮ اهـلا عـزيـزي** - {mention}\n\n"
        f"**⌔∮ يتـم الان اعـادة تشغيـل بـوت Mido فـي السيـرفـر قـد يستغـرق الامـر 2-3 دقيقـه ▬▭ ...**",
    )
    if cmd == "كلين":
        for file in exts:
            removing = glob.glob(f"./*.{file}")
            for i in removing:
                os.remove(i)
        for i in cmds:
            await _zedutils.runcmd(i)
    await event.client.reload(zed)
