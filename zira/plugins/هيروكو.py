# Heroku manager for your Mido

# CC- @refundisillegal\nSyntax:-\n.get var NAME\n.del var NAME\n.set var NAME

# Copyright (C) 2020 Adek Maulana.
# All rights reserved.

import asyncio
import math
import os

import heroku3
import requests
import urllib3

from . import zedub

from ..Config import Config
from ..core.managers import edit_delete, edit_or_reply

plugin_category = "الادوات"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# =================

Heroku = heroku3.from_key(Config.HEROKU_API_KEY)
heroku_api = "https://api.heroku.com"
HEROKU_APP_NAME = Config.HEROKU_APP_NAME
HEROKU_API_KEY = Config.HEROKU_API_KEY


@zedub.zed_cmd(
    pattern=r"(set|get|del) var ([\s\S]*)",
    command=("var", plugin_category),
    info={
        "header": "To manage heroku vars.",
        "flags": {
            "set": "To set new var in heroku or modify the old var",
            "get": "To show the already existing var value.",
            "del": "To delete the existing value",
        },
        "الاسـتخـدام": [
            "{tr}set var <var name> <var value>",
            "{tr}get var <var name>",
            "{tr}del var <var name>",
        ],
        "مثــال": [
            "{tr}get var ALIVE_NAME",
        ],
    },
)
async def variable(var):  # sourcery no-metrics
    """
    Manage most of ConfigVars setting, set new var, get current var, or delete var...
    """
    if (Config.HEROKU_API_KEY is None) or (Config.HEROKU_APP_NAME is None):
        return await edit_delete(
            var,
            "**- عــذراً .. لـديك خطـأ بالـفـارات**\n**-اذهـب الـى حسـابك هيـروكو ثم اعـدادات التطبيـق ثم الفـارات وقـم بالتـأكـد من الفـارات التـاليـه :**\n\n `HEROKU_API_KEY` \n `HEROKU_APP_NAME`",
        )
    app = Heroku.app(Config.HEROKU_APP_NAME)
    exe = var.pattern_match.group(1)
    heroku_var = app.config()
    if exe == "get":
        zed = await edit_or_reply(var, "**⌔∮ جاري الحصول على المعلومات. **")
        await asyncio.sleep(1.0)
        try:
            variable = var.pattern_match.group(2).split()[0]
            if variable in heroku_var:
                return await zed.edit(
                    "𓆩 𝑺𝑶𝑼𝑹𝑪𝑬 Mido - 𝑮𝑶𝑵𝑭𝑰𝑮 𝑽𝑨𝑹𝑺 𓆪\n**𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻**" f"\n\n**⌔∮الفــار** `{variable} = {heroku_var[variable]}` .\n"
                )
            await zed.edit(
                "𓆩 𝑺𝑶𝑼𝑹𝑪𝑬 Mido - 𝑮𝑶𝑵𝑭𝑰𝑮 𝑽𝑨𝑹𝑺 𓆪\n**𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻**" f"\n\n**⌔∮الفــار** `{variable}` غيــر مـوجــود ؟!"
            )
        except IndexError:
            configs = prettyjson(heroku_var.to_dict(), indent=2)
            with open("configs.json", "w") as fp:
                fp.write(configs)
            with open("configs.json", "r") as fp:
                result = fp.read()
                await edit_or_reply(
                    zed,
                    "`[HEROKU]` ConfigVars:\n\n"
                    "================================"
                    f"\n```{result}```\n"
                    "================================",
                )
            os.remove("configs.json")
    elif exe == "set":
        variable = "".join(var.text.split(maxsplit=2)[2:])
        zed = await edit_or_reply(var, "**⌔∮ جاري اعداد المعلومات**")
        if not variable:
            return await zed.edit("`.set var <ConfigVars-name> <value>`")
        value = "".join(variable.split(maxsplit=1)[1:])
        variable = "".join(variable.split(maxsplit=1)[0])
        if not value:
            return await zed.edit("`.set var <ConfigVars-name> <value>`")
        await asyncio.sleep(1.5)
        if variable in heroku_var:
            await zed.edit("**⌔∮ تم تغيـر** `{}` **:**\n **- المتغير :** `{}` \n**- يتم الان اعـادة تشغيـل بـوت Mido يستغـرق الامر 2-1 دقيقـه ▬▭ ...**".format(variable, value))
        else:
            await zed.edit("**⌔∮ تم اضافه** `{}` **:** \n**- المضاف اليه :** `{}` \n**يتم الان اعـادة تشغيـل بـوت Mido يستغـرق الامر 2-1 دقيقـه ▬▭ ...**".format(variable, value))
        heroku_var[variable] = value
    elif exe == "del":
        zed = await edit_or_reply(var, "⌔∮ الحصول على معلومات لحذف المتغير. ")
        try:
            variable = var.pattern_match.group(2).split()[0]
        except IndexError:
            return await zed.edit("⌔∮ يرجى تحديد `Configvars` تريد حذفها. ")
        await asyncio.sleep(1.5)
        if variable not in heroku_var:
            return await zed.edit(f"⌔∮ `{variable}`**  غير موجود**")

        await zed.edit(f"**⌔∮** `{variable}`  **تم حذفه بنجاح. \n**يتم الان اعـادة تشغيـل بـوت Mido يستغـرق الامر 2-1 دقيقـه ▬▭ ...**")
        del heroku_var[variable]


@zedub.zed_cmd(
    pattern=r"(ضع|جلب|حذف) فار ([\s\S]*)",
    command=("var", plugin_category),
    info={
        "header": "لـ اضـافـة وتغييـر فـارات هيـروكـو لحســابك",
        "الاوامــر": {
            "ضع": "لـ وضـع قيمـه جديـده لـ فـار محـدد",
            "جلب": "لـ جلـب قيمـة فـار محـدد",
            "حذف": "لـ حـذف قيمـة فـار محـدد",
        },
        "الاسـتخـدام": [
            "{tr}ضع فار <اسم الفار> <القيمه>",
            "{tr}جلب فار <اسم الفار>",
            "{tr}حذف فار <اسم الفار>",
        ],
        "مثــال": [
            "{tr}جلب فار ALIVE_NAME",
        ],
    },
)
async def variable(var):  # sourcery no-metrics
    """
    Manage most of ConfigVars setting, set new var, get current var, or delete var...
    """
    if (Config.HEROKU_API_KEY is None) or (Config.HEROKU_APP_NAME is None):
        return await edit_delete(
            var,
            "**- عــذراً .. لـديك خطـأ بالـفـارات**\n**-اذهـب الـى حسـابك هيـروكو ثم اعـدادات التطبيـق ثم الفـارات وقـم بالتـأكـد من الفـارات التـاليـه :**\n\n `HEROKU_API_KEY` \n `HEROKU_APP_NAME`",
        )
    app = Heroku.app(Config.HEROKU_APP_NAME)
    exe = var.pattern_match.group(1)
    heroku_var = app.config()
    if exe == "جلب":
        zed = await edit_or_reply(var, "**⌔∮ جاري الحصول على المعلومات. **")
        await asyncio.sleep(1.0)
        try:
            variable = var.pattern_match.group(2).split()[0]
            if variable in heroku_var:
                return await zed.edit(
                    "𓆩 𝑺𝑶𝑼𝑹𝑪𝑬 Mido - 𝑮𝑶𝑵𝑭𝑰𝑮 𝑽𝑨𝑹𝑺 𓆪\n**𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻**" f"\n\n**⌔∮الفــار** `{variable} = {heroku_var[variable]}` .\n"
                )
            await zed.edit(
                "𓆩 𝑺𝑶𝑼𝑹𝑪𝑬 Mido - 𝑮𝑶𝑵𝑭𝑰𝑮 𝑽𝑨𝑹𝑺 𓆪\n**𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻**" f"\n\n**⌔∮الفــار** `{variable}` غيــر مـوجــود ؟!"
            )
        except IndexError:
            configs = prettyjson(heroku_var.to_dict(), indent=2)
            with open("configs.json", "w") as fp:
                fp.write(configs)
            with open("configs.json", "r") as fp:
                result = fp.read()
                await edit_or_reply(
                    zed,
                    "`[HEROKU]` ConfigVars:\n\n"
                    "================================"
                    f"\n```{result}```\n"
                    "================================",
                )
            os.remove("configs.json")
    elif exe == "ضع":
        variable = "".join(var.text.split(maxsplit=2)[2:])
        zed = await edit_or_reply(var, "**⌔∮ جاري اعداد المعلومات**")
        if not variable:
            return await zed.edit("`.set var <ConfigVars-name> <value>`")
        value = "".join(variable.split(maxsplit=1)[1:])
        variable = "".join(variable.split(maxsplit=1)[0])
        if not value:
            return await zed.edit("`.set var <ConfigVars-name> <value>`")
        await asyncio.sleep(1.5)
        if variable in heroku_var:
            await zed.edit("**⌔∮ تم تغيـر** `{}` **:**\n **- المتغير :** `{}` \n**- يتم الان اعـادة تشغيـل بـوت Mido يستغـرق الامر 2-1 دقيقـه ▬▭ ...**".format(variable, value))
        else:
            await zed.edit("**⌔∮ تم اضافه** `{}` **:** \n**- المضاف اليه :** `{}` \n**يتم الان اعـادة تشغيـل بـوت Mido يستغـرق الامر 2-1 دقيقـه ▬▭ ...**".format(variable, value))
        heroku_var[variable] = value
    elif exe == "حذف":
        zed = await edit_or_reply(var, "⌔∮ الحصول على معلومات لحذف المتغير. ")
        try:
            variable = var.pattern_match.group(2).split()[0]
        except IndexError:
            return await zed.edit("⌔∮ يرجى تحديد `Configvars` تريد حذفها. ")
        await asyncio.sleep(1.5)
        if variable not in heroku_var:
            return await zed.edit(f"⌔∮ `{variable}`**  غير موجود**")

        await zed.edit(f"**⌔∮** `{variable}`  **تم حذفه بنجاح. \n**يتم الان اعـادة تشغيـل بـوت Mido يستغـرق الامر 2-1 دقيقـه ▬▭ ...**")
        del heroku_var[variable]



@zedub.zed_cmd(
    pattern="اسستخدامي$",
    command=("اسستخدامي", plugin_category),
    info={
        "header": "لـ عـرض سـاعـات استخـدامك الكـليـه والمتبقيـه",
        "الاسـتخـدام": "{tr}اسستخدامي",
    },
)
async def dyno_usage(dyno):
    """
    لـ عـرض سـاعـات استخـدامك الكـليـه والمتبقيـه
    """
    if (HEROKU_APP_NAME is None) or (HEROKU_API_KEY is None):
        return await edit_delete(
            dyno,
            "**- عــذراً .. لـديك خطـأ بالـفـارات**\n**-اذهـب الـى حسـابك هيـروكو ثم اعـدادات التطبيـق ثم الفـارات وقـم بالتـأكـد من الفـارات التـاليـه :**\n\n `HEROKU_API_KEY` \n `HEROKU_APP_NAME`",
        )
    dyno = await edit_or_reply(dyno, "**⌔∮ جــاري المعـالجـه ...**")
    useragent = (
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/80.0.3987.149 Mobile Safari/537.36"
    )
    user_id = Heroku.account().id
    headers = {
        "User-Agent": useragent,
        "Authorization": f"Bearer {Config.HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3.account-quotas",
    }
    path = f"/accounts/{user_id}/actions/get-quota"
    r = requests.get(heroku_api + path, headers=headers)
    if r.status_code != 200:
        return await dyno.edit(
            "⌔∮ خطا:** شي سيء قد حدث **\n" f" ⌔∮ `{r.reason}`\n"
        )
    result = r.json()
    quota = result["account_quota"]
    quota_used = result["quota_used"]

    # - Used -
    remaining_quota = quota - quota_used
    percentage = math.floor(remaining_quota / quota * 100)
    minutes_remaining = remaining_quota / 60
    hours = math.floor(minutes_remaining / 60)
    minutes = math.floor(minutes_remaining % 60)
    # - Current -
    App = result["apps"]
    try:
        App[0]["quota_used"]
    except IndexError:
        AppQuotaUsed = 0
        AppPercentage = 0
    else:
        AppQuotaUsed = App[0]["quota_used"] / 60
        AppPercentage = math.floor(App[0]["quota_used"] * 100 / quota)
    AppHours = math.floor(AppQuotaUsed / 60)
    AppMinutes = math.floor(AppQuotaUsed % 60)
    await asyncio.sleep(1.5)
    return await dyno.edit(
        "𓆩 𝑺𝑶𝑼𝑹𝑪𝑬 Mido - 𝑫𝒀𝑵𝑶 𝑼𝑺𝑨𝑮𝑬 𓆪\n𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻\n\n"
        f"**⌔∮ اسم التطبيق في هيروكو :**\n"
        f"**    - معرف اشتراكك ⪼ {Config.HEROKU_APP_NAME}**"
        f"\n\n"
        f" **⌔∮ مدة اسـتخدامك لبوت Mido : **\n"
        f"     -  `{AppHours}`**ساعه**  `{AppMinutes}`**دقيقه**  "
        f"**⪼**  `{AppPercentage}`**%**"
        "\n\n"
        " **⌔∮ الساعات المتبقيه لاستخدامك : **\n"
        f"     -  `{hours}`**ساعه**  `{minutes}`**دقيقه**  "
        f"**⪼**  `{percentage}`**%**"
    )


@zedub.zed_cmd(
    pattern="(سجل التنصيب|السجلات)$",
    command=("سجل التنصيب", plugin_category),
    info={
        "header": "لـ جلـب آخـر 100 سطـر مـن سجـل تنصيبـك",
        "الاسـتخـدام": ["{tr}سجل التنصيب", "{tr}السجلات"],
    },
)
async def _(dyno):
    "To get recent 100 lines logs from heroku"
    if (HEROKU_APP_NAME is None) or (HEROKU_API_KEY is None):
        return await edit_delete(
            dyno,
            "**- عــذراً .. لـديك خطـأ بالـفـارات**\n**-اذهـب الـى حسـابك هيـروكو ثم اعـدادات التطبيـق ثم الفـارات وقـم بالتـأكـد من الفـارات التـاليـه :**\n\n `HEROKU_API_KEY` \n `HEROKU_APP_NAME`",
        )
    try:
        Heroku = heroku3.from_key(HEROKU_API_KEY)
        app = Heroku.app(HEROKU_APP_NAME)
    except BaseException:
        return await dyno.reply(
            " Please make sure your Heroku API Key, Your App name are configured correctly in the heroku"
        )
    data = app.get_log()
    await edit_or_reply(
        dyno, data, deflink=True, linktext="**-آخـر 100 سطـر مـن سجـلات تنصيبـك :**"
    )


def prettyjson(obj, indent=2, maxlinelength=80):
    """Renders JSON content with indentation and line splits/concatenations to fit maxlinelength.
    Only dicts, lists and basic types are supported"""
    items, _ = getsubitems(
        obj,
        itemkey="",
        islast=True,
        maxlinelength=maxlinelength - indent,
        indent=indent,
    )
    return indentitems(items, indent, level=0)
