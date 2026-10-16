from PIL import Image, ImageDraw, ImageFont
from validators.url import url
from zira.helpers.utils.http import aget, apost


async def fakegs(search, result):
    imgurl = "https://i.imgur.com/wNFr5X2.jpg"
    with open("./temp/temp.jpg", "wb") as f:
        f.write((await aget(imgurl)).content)
    img = Image.open("./temp/temp.jpg")
    drawing = ImageDraw.Draw(img)
    blue = (0, 0, 255)
    black = (0, 0, 0)
    font1 = ImageFont.truetype("zira/helpers/styles/ProductSans-BoldItalic.ttf", 20)
    font2 = ImageFont.truetype("zira/helpers/styles/ProductSans-Light.ttf", 23)
    drawing.text((450, 258), result, fill=blue, font=font1)
    drawing.text((270, 37), search, fill=black, font=font2)
    img.save("./temp/temp.jpg")
    return "./temp/temp.jpg"


async def trumptweet(text):
    r = (await aget(
        f"https://nekobot.xyz/api/imagegen?type=trumptweet&text={text}"
    )).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png").convert("RGB")
    img.save("temp.webp", "webp")
    return "temp.webp"


async def changemymind(text):
    r = (await aget(
        f"https://nekobot.xyz/api/imagegen?type=changemymind&text={text}"
    )).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png").convert("RGB")
    img.save("temp.jpg", "jpeg")
    return "temp.jpg"


async def kannagen(text):
    r = (await aget(
        f"https://nekobot.xyz/api/imagegen?type=kannagen&text={text}"
    )).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png").convert("RGB")
    img.save("temp.webp", "webp")
    return "temp.webp"


async def moditweet(text):
    r = (await aget(
        f"https://nekobot.xyz/api/imagegen?type=tweet&text={text}&username=narendramodi"
    )).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png").convert("RGB")
    img.save("temp.webp", "webp")
    return "temp.webp"


async def tweets(text1, text2):
    r = (await aget(
        f"https://nekobot.xyz/api/imagegen?type=tweet&text={text1}&username={text2}"
    )).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png").convert("RGB")
    img.save("temp.webp", "webp")
    return "temp.webp"


async def iphonex(text):
    r = (await aget(f"https://nekobot.xyz/api/imagegen?type=iphonex&url={text}")).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png").convert("RGB")
    img.save("temp.jpg", "jpeg")
    return "temp.jpg"


async def baguette(text):
    r = (await aget(
        f"https://nekobot.xyz/api/imagegen?type=baguette&url={text}"
    )).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png").convert("RGB")
    img.save("temp.jpg", "jpeg")
    return "temp.jpg"


async def threats(text):
    r = (await aget(f"https://nekobot.xyz/api/imagegen?type=threats&url={text}")).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png")
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save("temp.jpg", "jpeg")
    return "temp.jpg"


async def lolice(text):
    r = (await aget(f"https://nekobot.xyz/api/imagegen?type=lolice&url={text}")).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png")
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save("temp.jpg", "jpeg")
    return "temp.jpg"


async def trash(text):
    r = (await aget(f"https://nekobot.xyz/api/imagegen?type=trash&url={text}")).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png")
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save("temp.jpg", "jpeg")
    return "temp.jpg"


async def awooify(text):
    r = (await aget(f"https://nekobot.xyz/api/imagegen?type=awooify&url={text}")).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png")
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save("temp.jpg", "jpeg")
    return "temp.jpg"


async def trap(text1, text2, text3):
    r = (await aget(
        f"https://nekobot.xyz/api/imagegen?type=trap&name={text1}&author={text2}&image={text3}"
    )).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png")
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save("temp.jpg", "jpeg")
    return "temp.jpg"


async def phcomment(text1, text2, text3):
    r = (await aget(
        f"https://nekobot.xyz/api/imagegen?type=phcomment&image={text1}&text={text2}&username={text3}"
    )).json()
    sandy = r.get("message")
    zedurl = url(sandy)
    if not zedurl:
        return "check syntax once more"
    with open("temp.png", "wb") as f:
        f.write((await aget(sandy)).content)
    img = Image.open("temp.png")
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save("temp.jpg", "jpeg")
    return "temp.jpg"
