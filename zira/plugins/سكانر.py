# =========================================================== #
#                                                             Mido                                                                 #

"""امـر استخـراج النص من الصـوره
كتابـة وتطويـر الكـود لـ Mido الهيبـه 
حقـــوق Mido™ """

#                                                             Mido                                                                 #
# =========================================================== #
import json
import os
from PIL import Image
from googletrans import LANGUAGES

from ..Config import Config
from ..core.managers import edit_delete, edit_or_reply
from ..helpers.functions import getTranslate
from ..sql_helper.globals import gvarstatus
from . import Convert, zedub, soft_deEmojify
from ..helpers.utils.http import apost

plugin_category = "الادوات"

glist = ["انكلش", "عربي", "بلغاري", "صيني", "صيني2", "كرواتي", "Czech", "Danish", "Dutch", "فيني", "فرنسي", "الماني", "يوناني", "هنغاري", "كوري", "ايطالي", "ياباني", "بولندي", "برتغالي", "روسي", "سلوفاني", "اسباني", "سويدي", "تركي"]
oldlang = {
    "انكلش": "eng",
    "عربي": "ara",
    "بلغاري": "bul",
    "صيني": "chs",
    "صيني2": "cht",
    "كرواتي": "hrv",
    "Czech": "cze",
    "Danish": "dan",
    "Dutch": "dut",
    "فيني": "fin",
    "فرنسي": "fre",
    "الماني": "ger",
    "يوناني": "gre",
    "هنغاري": "hun",
    "كوري": "kor",
    "ايطالي": "ita",
    "ياباني": "jpn",
    "بولندي": "pol",
    "برتغالي": "por",
    "روسي": "rus",
    "سلوفاني": "slv",
    "اسباني": "spa",
    "سويدي": "swe",
    "تركي": "tur",
}

def conv_image(image):
    im = Image.open(image)
    im.save(image, "PNG")
    new_file_name = image + ".png"
    os.rename(image, new_file_name)
    return new_file_name


async def ocr_space_file(filename, overlay=False, api_key=Config.OCR_SPACE_API_KEY, language='eng'):
    """ OCR.space API request with local file.
        Python3.5 - not tested on 2.7
    :param filename: Your file path & name.
    :param overlay: Is OCR.space overlay required in your response.
                    Defaults to False.
    :param api_key: OCR.space API key.
                    Defaults to 'helloworld'.
    :param language: Language code to be used in OCR.
                    List of available language codes can be found on https://ocr.space/OCRAPI
                    Defaults to 'en'.
    :return: Result in JSON format.
    """

    payload = {'isOverlayRequired': overlay,
               'apikey': api_key,
               'language': language,
               }
    with open(filename, 'rb') as f:
        r = await apost('https://api.ocr.space/parse/image',
                        files={filename: f},
                        data=payload,
                        )
    return r.json()


async def ocr_space_url(url, overlay=False, api_key=Config.OCR_SPACE_API_KEY, language='eng'):
    """ OCR.space API request with remote file.
        Python3.5 - not tested on 2.7
    :param url: Image url.
    :param overlay: Is OCR.space overlay required in your response.
                    Defaults to False.
    :param api_key: OCR.space API key.
                    Defaults to 'helloworld'.
    :param language: Language code to be used in OCR.
                    List of available language codes can be found on https://ocr.space/OCRAPI
                    Defaults to 'en'.
    :return: Result in JSON format.
    """

    payload = {'url': url,
               'isOverlayRequired': overlay,
               'apikey': api_key,
               'language': language,
               }
    r = await apost('https://api.ocr.space/parse/image',
                    data=payload,
                    )
    return r.json()


def progress(current, total):
    logger.info("Downloaded {} of {}\nCompleted {}".format(
        current, total, (current / total) * 100))


@zedub.zed_cmd(pattern="اللغات")
async def get_ocr_languages(event):
    if event.fwd_from:
        return
    languages = {
        "انكلش": "eng",
        "عربي": "ara",
        "بلغاري": "bul",
        "صيني": "chs",
        "صيني2": "cht",
        "كرواتي": "hrv",
        "Czech": "cze",
        "Danish": "dan",
        "Dutch": "dut",
        "فيني": "fin",
        "فرنسي": "fre",
        "الماني": "ger",
        "يوناني": "gre",
        "هنغاري": "hun",
        "كوري": "kor",
        "ايطالي": "ita",
        "ياباني": "jpn",
        "بولندي": "pol",
        "برتغالي": "por",
        "روسي": "rus",
        "سلوفاني": "slv",
        "اسباني": "spa",
        "سويدي": "swe",
        "تركي": "tur",
    }
    a = json.dumps(languages, sort_keys=True, indent=4)
    await event.edit(str(a))


@zedub.zed_cmd(pattern="النص (.*)")
async def parse_ocr_space_api(event):
    if event.fwd_from:
        return
    await event.edit("**⎉╎جـارِ جلب النص من الميديـا ▬▭ ...**")
    if not os.path.isdir(Config.TEMP_DIR):
        os.makedirs(Config.TEMP_DIR)
    lang_code = event.pattern_match.group(1)
    if lang_code in glist:
        if lang_code in oldlang:
            langcode = oldlang[lang_code]
    downloaded_file_name = await zedub.download_media(
        await event.get_reply_message(),
        Config.TEMP_DIR
    )
    if downloaded_file_name.endswith((".webp")):
        downloaded_file_name = conv_image(downloaded_file_name)
    test_file = await ocr_space_file(filename=downloaded_file_name, language=langcode)
    ParsedText = "hmm"
    try:
        ParsedText = test_file["ParsedResults"][0]["ParsedText"]
        ProcessingTimeInMilliseconds = str(int(test_file["ProcessingTimeInMilliseconds"]) // 1000)
    except Exception as e:
        await event.edit("**- اووبـس حدث خطـأ :**\n**-الخطأ :** `{}`\n`{}`".format(str(e), json.dumps(test_file, sort_keys=True, indent=4)))
    else:
        await event.edit("**⎉╎تم جلب النص من الميديـا\n**⎉╎خـلال {} ثـانيـه...**\n\n`{}`".format(ProcessingTimeInMilliseconds, ParsedText))
    os.remove(downloaded_file_name)
    await event.edit(ParsedText)



@zedub.zed_cmd(
    pattern=r"(|ا)سكانر(?:\s|$)([\s\S]*)",
    command=("ocr", plugin_category),
    info={
        "header": "To read text in image/gif/sticker/video and print it.",
        "description": "Reply to an image or sticker to extract text from it.\n\nGet language codes from [here](https://ocr.space/ocrapi).",
        "usage": "{tr}ocr <language code>",
        "examples": "{tr}ocr eng",
    },
)
async def ocr(event):
    "To read text in media."
    reply = await event.get_reply_message()
    if not event.reply_to_msg_id or not reply.media:
        return await edit_delete(event, "**- بالـرد ع ميديـا لاستخـراج النص منهـا ...**")
    zevent = await edit_or_reply(event, "**⎉╎جـارِ جلب النص من الميديـا ▬▭ ...**")
    if not os.path.isdir(Config.TEMP_DIR):
        os.makedirs(Config.TEMP_DIR)
    cmd = event.pattern_match.group(1)
    lang_code = event.pattern_match.group(2)
    output_file = await Convert.to_image(
        event, reply, dirct="./temp", file="image.png", rgb=True, noedits=True
    )
    if not output_file[1]:
        return await edit_delete(
            zevent, "**- هل انت متأكد من ان هذه صـورة ؟!**"
        )
    if lang_code in glist:
        if lang_code in oldlang:
            langcode = oldlang[lang_code]
    test_file = await ocr_space_file(filename=output_file[1], language=langcode)
    try:
        ParsedText = test_file["ParsedResults"][0]["ParsedText"]
    except Exception:
        await edit_delete(
            zevent, "**- لا يمكنني قراءة النص**\n**- يبدو ان النص غير واضحـاً ؟!**"
        )
    else:
        if cmd == "":
            await edit_or_reply(
                zevent, f"**- تم نسـخ النص من ملف الميديـا :**\n\n`{ParsedText}`"
            )
        if cmd == "ا":
            TRT_LANG = langcode or "en"
            try:
                reply_text = await getTranslate(
                    soft_deEmojify(ParsedText), dest=TRT_LANG
                )
            except ValueError:
                return await edit_delete(zevent, "**- حدث خطـأ بالتعـرف على اللغـه ؟!**")
            source_lan = LANGUAGES[f"{reply_text.src.lower()}"]
            transl_lan = LANGUAGES[f"{reply_text.dest.lower()}"]
            tran_text = f"📜**الترجمـة :-\n- مـن {source_lan.title()}({reply_text.src.lower()}) الـى {transl_lan.title()}({reply_text.dest.lower()}) :**\n\n`{reply_text.text}`"
            await edit_or_reply(
                zevent,
                f"🧧**- تم نسـخ النص من ملف الميديـا :**\n\n`{ParsedText}`\n\n{tran_text}",
            )
    if os.path.exists(output_file[1]):
        os.remove(output_file[1])


@zedub.zed_cmd(
    pattern="اسكانر",
    command=("tocr", plugin_category),
    info={
        "header": "To read text in image/gif/sticker/video and print it with its translation.",
        "description": "Reply to an image/gif/sticker/video to extract text from it and print it with its translation.\n\nGet language codes from [here](https://ocr.space/ocrapi).",
        "note": "for this command transalted language set lanuage by `.lang tocr` command.",
        "usage": "{tr}tocr <language code>",
        "examples": "{tr}tocr eng",
    },
)
async def ocr(event):
    "To read text in media & paste with translated."
