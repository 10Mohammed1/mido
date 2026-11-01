import asyncio
import os

from PIL import Image, ImageDraw, ImageFont

from ..core.managers import edit_delete, edit_or_reply
from . import *
from . import BOTLOG, BOTLOG_CHATID, mention, zedub

plugin_category = "الترفيه"


def text_set(text):
    lines = []
    if len(text) <= 55:
        lines.append(text)
    else:
        all_lines = text.split("\n")
        for line in all_lines:
            if len(line) <= 55:
                lines.append(line)
            else:
                k = int(len(line) / 55)
                for z in range(1, k + 2):
                    lines.append(line[((z - 1) * 55) : (z * 55)])
    return lines


@zedub.zed_cmd(pattern="رساله ?(.*)")
async def writer(e):
    if e.reply_to:
        reply = await e.get_reply_message()
        text = reply.message
    elif e.pattern_match.group(1):
        text = e.text.split(maxsplit=1)[1]
    else:
        return await e.edit("**- بالـرد على نص او .رساله + النص**")
    img = Image.open("zedthon/malath/ppmsg.jpg")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("zedthon/malath/zarz.ttf", 30)
    x, y = 150, 140
    all_lines = text_set(text)
    # The canvas is fixed-size, so only the first 25 lines fit; anything
    # beyond that is reported to the user instead of vanishing silently.
    lines = all_lines[:25]
    # Pillow >= 10 removed font.getsize(); getbbox returns (x0, y0, x1, y1).
    _hb = font.getbbox("hg")
    line_height = _hb[3] - _hb[1]
    for line in lines:
        draw.text((x, y), line, fill=(1, 22, 55), font=font)
        y = y + line_height - 5
    # Unique name so two concurrent commands cannot delete each other's file.
    file = f"Mido_{e.id}.jpg"
    img.save(file)
    caption = ""
    if len(all_lines) > len(lines):
        caption = f"**- تـم عـرض {len(lines)} سطـراً مـن {len(all_lines)}** **(حدود حجم الصورة)**"
    await e.reply(file=file, caption=caption)
    os.remove(file)
    await e.delete()


@zedub.zed_cmd(pattern=r"^\:/$")
async def kek(keks):
    keks = await edit_or_reply(keks, ":\\")
    uio = ["/", "\\"]
    for i in range(15):
        await asyncio.sleep(0.5)
        txt = ":" + uio[i % 2]
        await keks.edit(txt)


@zedub.zed_cmd(pattern=r"^\-_-$")
async def lol(lel):
    lel = await edit_or_reply(lel, "-__-")
    okay = "-__-"
    for _ in range(15):
        await asyncio.sleep(0.5)
        okay = okay[:-1] + "_-"
        await lel.edit(okay)


@zedub.zed_cmd(pattern=r"^\;_;$")
async def fun(e):
    e = await edit_or_reply(e, ";__;")
    t = ";__;"
    for _ in range(15):
        await asyncio.sleep(0.5)
        t = t[:-1] + "_;"
        await e.edit(t)


@zedub.zed_cmd(pattern="oof$")
async def Oof(e):
    t = "Oof"
    catevent = await edit_or_reply(e, t)
    for _ in range(15):
        await asyncio.sleep(0.5)
        t = t[:-1] + "of"
        await catevent.edit(t)


@zedub.zed_cmd(pattern="اكتب (.*)")
async def typewriter(typew):
    message = typew.pattern_match.group(1)
    sleep_time = 0.2
    typing_symbol = "|"
    old_text = ""
    typew = await edit_or_reply(typew, typing_symbol)
    await asyncio.sleep(sleep_time)
    for character in message:
        old_text = old_text + "" + character
        typing_text = old_text + "" + typing_symbol
        await typew.edit(typing_text)
        await asyncio.sleep(sleep_time)
        await typew.edit(old_text)
        await asyncio.sleep(sleep_time)


@zedub.zed_cmd(pattern=r"كرر (\d*) (.*)")
async def _(event):
    if event.fwd_from:
        return
    zed = ("".join(event.text.split(maxsplit=1)[1:])).split(" ", 1)
    message = zed[1]
    count = int(zed[0])
    repmessage = (f"{message} ") * count
    await asyncio.wait([event.respond(repmessage)])
    await event.delete()


@zedub.zed_cmd(pattern="ميمي")
async def meme(event):
    memeVar = event.text
    sleepValue = 0.5
    memeVar = memeVar[6:]
    if not memeVar:
        memeVar = "✈️"
    event = await edit_or_reply(event, "-------------" + memeVar)
    await asyncio.sleep(sleepValue)
    await event.edit("------------" + memeVar + "-")
    await asyncio.sleep(sleepValue)
    await event.edit("-----------" + memeVar + "--")
    await asyncio.sleep(sleepValue)
    await event.edit("----------" + memeVar + "---")
    await asyncio.sleep(sleepValue)
    await event.edit("---------" + memeVar + "----")
    await asyncio.sleep(sleepValue)
    await event.edit("--------" + memeVar + "-----")
    await asyncio.sleep(sleepValue)
    await event.edit("-------" + memeVar + "------")
    await asyncio.sleep(sleepValue)
    await event.edit("------" + memeVar + "-------")
    await asyncio.sleep(sleepValue)
    await event.edit("-----" + memeVar + "--------")
    await asyncio.sleep(sleepValue)
    await event.edit("----" + memeVar + "---------")
    await asyncio.sleep(sleepValue)
    await event.edit("---" + memeVar + "----------")
    await asyncio.sleep(sleepValue)
    await event.edit("--" + memeVar + "-----------")
    await asyncio.sleep(sleepValue)
    await event.edit("-" + memeVar + "------------")
    await asyncio.sleep(sleepValue)
    await event.edit(memeVar + "-------------")
    await asyncio.sleep(sleepValue)
    await event.edit("-------------" + memeVar)
    await asyncio.sleep(sleepValue)
    await event.edit("------------" + memeVar + "-")
    await asyncio.sleep(sleepValue)
    await event.edit("-----------" + memeVar + "--")
    await asyncio.sleep(sleepValue)
    await event.edit("----------" + memeVar + "---")
    await asyncio.sleep(sleepValue)
    await event.edit("---------" + memeVar + "----")
    await asyncio.sleep(sleepValue)
    await event.edit("--------" + memeVar + "-----")
    await asyncio.sleep(sleepValue)
    await event.edit("-------" + memeVar + "------")
    await asyncio.sleep(sleepValue)
    await event.edit("------" + memeVar + "-------")
    await asyncio.sleep(sleepValue)
    await event.edit("-----" + memeVar + "--------")
    await asyncio.sleep(sleepValue)
    await event.edit("----" + memeVar + "---------")
    await asyncio.sleep(sleepValue)
    await event.edit("---" + memeVar + "----------")
    await asyncio.sleep(sleepValue)
    await event.edit("--" + memeVar + "-----------")
    await asyncio.sleep(sleepValue)
    await event.edit("-" + memeVar + "------------")
    await asyncio.sleep(sleepValue)
    await event.edit(memeVar + "-------------")
    await asyncio.sleep(sleepValue)
    await event.edit(memeVar)


@zedub.zed_cmd(pattern="جف")
async def give(event):
    if event.fwd_from:
        return
    giveVar = event.text
    sleepValue = 0.5
    lp = giveVar[6:]
    if not lp:
        lp = " 🍭"
    event = await edit_or_reply(event, lp + "        ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + "       ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + "      ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + "     ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + lp + "    ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + lp + lp + "   ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + lp + lp + lp + "  ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + lp + lp + lp + lp + " ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + lp + lp + lp + lp + lp)
    await asyncio.sleep(sleepValue)
    await event.edit(lp + "        ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + "       ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + "      ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + "     ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + lp + "    ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + lp + lp + "   ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + lp + lp + lp + "  ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + lp + lp + lp + lp + " ")
    await asyncio.sleep(sleepValue)
    await event.edit(lp + lp + lp + lp + lp + lp + lp + lp + lp)
