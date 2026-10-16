import os
import random

from telethon.errors.rpcerrorlist import UsernameOccupiedError
from telethon.tl import functions
from telethon.tl.functions.account import UpdateUsernameRequest
from telethon.tl.functions.channels import GetAdminedPublicChannelsRequest
from telethon.tl.functions.photos import DeletePhotosRequest, GetUserPhotosRequest
from telethon.tl.types import Channel, Chat, InputPhoto, User, InputMessagesFilterEmpty

from . import zedub

from ..Config import Config
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply

LOGS = logging.getLogger(__name__)

# =========================================================== #
#                                                             Mido
# =========================================================== #
BIO_OK = "**⎉╎تم تغييـر بايـو حسـابك .. بنجـاح ✅**"
NAME_OK = "**⎉╎تم تغييـر إسـم حسـابك .. بنجـاح ✅**"
USERNAME_OK = "**⎉╎تم تغييـر يـوزر حسـابك .. بنجـاح ✅**"
PP_CHANGED = "**⎉╎تم تغييـر صـورة حسـابك .. بنجـاح ✅**"
USERNAME_TAKEN = "**⎉╎هـذا اليـوزر مستخـدم ؟!**"
PP_TOO_SMOL = "** ⎉╎هذه الصورة صغيرة جداً قم بـ اختيار صورة أخرى**"
PP_ERROR = "** ⎉╎حدث خطا اثناء معالجه الصوره  ⌁**"
INVALID_MEDIA = "⎉╎امتداد هذه الصورة غير صالح"
# =========================================================== #
#                                                             Mido
# =========================================================== #

@zedub.zed_cmd(pattern="ضع بايو(?: |$)(.*)")
async def _(event):
    bio = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not bio and reply:
        bio = reply.text
    if not bio:
        return await edit_delete(event, "**- ارسـل (.ضع بايو) + البايـو او بالـرد ع البايـو**", 10)
    try:
        await event.client(functions.account.UpdateProfileRequest(about=bio))
        await edit_delete(event, BIO_OK)
    except Exception as e:
        await edit_or_reply(event, f"**خطأ:**\n`{str(e)}`")


@zedub.zed_cmd(pattern="ضع اسم(?: |$)(.*)")
async def _(event):
    names = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not names and reply:
        names = reply.text
    if not names:
        return await edit_delete(event, "**- ارسـل (.ضع اسم) + الاسـم او بالـرد ع الاسـم**", 10)
    first_name = names
    last_name = ""
    if ";" in names:
        first_name, last_name = names.split("|", 1)
    try:
        await event.client(
            functions.account.UpdateProfileRequest(
                first_name=first_name, last_name=last_name
            )
        )
        await edit_delete(event, NAME_OK)
    except Exception as e:
        await edit_or_reply(event, f"**خطأ:**\n`{str(e)}`")


@zedub.zed_cmd(pattern="ضع صورة$")
async def _(event):
    reply_message = await event.get_reply_message()
    if not reply_message:
        return await edit_delete(event, "**- ارســل (.ضع صورة) بالــرد ع الصـورة**", 10)
    reply_message = await event.get_reply_message()
    catevent = await edit_or_reply(
        event, "**...**"
    )
    if not os.path.isdir(Config.TMP_DOWNLOAD_DIRECTORY):
        os.makedirs(Config.TMP_DOWNLOAD_DIRECTORY)
    photo = None
    try:
        photo = await event.client.download_media(
            reply_message, Config.TMP_DOWNLOAD_DIRECTORY
        )
    except Exception as e:
        await catevent.edit(str(e))
    else:
        if photo:
            await catevent.edit("⎉╎أنتـظر قلـيلا ")
            if photo.endswith((".mp4", ".MP4")):
                # https://t.me/tgbetachat/324694
                size = os.stat(photo).st_size
                if size > 2097152:
                    await catevent.edit("⎉╎يجب ان يكون الحجم اقل من 2 ميغا ✅")
                    os.remove(photo)
                    return
                catpic = None
                catvideo = await event.client.upload_file(photo)
            else:
                catpic = await event.client.upload_file(photo)
                catvideo = None
            try:
                await event.client(
                    functions.photos.UploadProfilePhotoRequest(
                        file=catpic, video=catvideo, video_start_ts=0.01
                    )
                )
            except Exception as e:
                await catevent.edit(f"**خطأ:**\n`{str(e)}`")
            else:
                await edit_or_reply(catevent, PP_CHANGED)
    try:
        os.remove(photo)
    except Exception as e:
        LOGS.info(str(e))


@zedub.zed_cmd(pattern="(ضع معرف|ضع يوزر)(?: |$)(.*)")
async def update_username(username):
    newusername = username.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not newusername and reply:
        newusername = reply.text
    if not newusername:
        return await edit_delete(event, "**- ارسـل (.ضع يوزر) + اليـوزر او بالـرد ع اليـوزر**", 10)
    try:
        await username.client(UpdateUsernameRequest(newusername))
        await edit_delete(event, USERNAME_OK)
    except UsernameOccupiedError:
        await edit_or_reply(event, USERNAME_TAKEN)
    except Exception as e:
        await edit_or_reply(event, f"**خطأ:**\n`{str(e)}`")


@zedub.zed_cmd(pattern="الحساب$")
async def count(event):
    u = 0
    g = 0
    c = 0
    bc = 0
    b = 0
    result = ""
    catevent = await edit_or_reply(event, "**⎉╎يتم الحساب ... انتظر**")
    dialogs = await event.client.get_dialogs(limit=None, ignore_migrated=True)
    for d in dialogs:
        currrent_entity = d.entity
        if isinstance(currrent_entity, User):
            if currrent_entity.bot:
                b += 1
            else:
                u += 1
        elif isinstance(currrent_entity, Chat):
            g += 1
        elif isinstance(currrent_entity, Channel):
            if currrent_entity.broadcast:
                bc += 1
            else:
                c += 1
        else:
            LOGS.info(d)

    result += f"**⎉╎الأشخاص:**\t**{u}**\n"
    result += f"**⎉╎الـمجموعات:**\t**{g}**\n"
    result += f"**⎉╎المجموعات الخارقه:**\t**{c}**\n"
    result += f"**⎉╎القنوات:**\t**{bc}**\n"
    result += f"**⎉╎البوتات:**\t**{b}**"

    await catevent.edit(result)


@zedub.zed_cmd(pattern="حذف صوره ?(.*)")
async def remove_profilepic(delpfp):
#.حذف صوره <رقم الصورة> | .حذف صوره
    group = delpfp.text[8:]
    if group == "الكل":
        lim = 0
    elif group.isdigit():
        lim = int(group)
    else:
        lim = 1
    pfplist = await delpfp.client(
        GetUserPhotosRequest(user_id=delpfp.sender_id, offset=0, max_id=0, limit=lim)
    )
    input_photos = [
        InputPhoto(
            id=sep.id,
            access_hash=sep.access_hash,
            file_reference=sep.file_reference,
        )
        for sep in pfplist.photos
    ]
    await delpfp.client(DeletePhotosRequest(id=input_photos))
    await edit_delete(
        delpfp, f"**⎉╎تـم حـذف الصـورة رقـم** {len(input_photos)}\n**⎉╎مـن حسـابك .. بنجـاح ✅**"
    )


@zedub.zed_cmd(pattern="انشائي$")
async def _(event):
    result = await event.client(GetAdminedPublicChannelsRequest())
    output_str = "**⎉╎جميع القنوات والمجموعات التي قمت بأنشائها :**\n"
    output_str += "".join(
        f" - {channel_obj.title} @{channel_obj.username} \n"
        for channel_obj in result.chats
    )
    await edit_or_reply(event, output_str)
