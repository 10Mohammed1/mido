import html
import re

from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from telethon.utils import get_display_name

from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..sql_helper import blacklist_sql as spl
from ..sql_helper import warns_sql as sql
from ..utils import is_admin
from . import BOTLOG_CHATID, zedub

logger = logging.getLogger(__name__)

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)


async def _apply_warn_punishment(event, target_id, soft_warn, limit):
    """ينفّذ الطرد (soft) أو الحظر (hard) بعد تجاوز حد التحذيرات.

    يفحص أولاً: أن الهدف ليس حساب البوت ولا مشرفاً، وأن يملك البوت
    صلاحية الحظر. كل تنفيذ أو فشل يُسجَّل في سجل الأوامر (BOTLOG).
    """
    client = event.client
    chat_id = event.chat_id
    action = "طرد" if soft_warn else "حظر"
    me = await client.get_me()
    if target_id == me.uid:
        logger.warning("warn-limit: تخطّي %s في %s — الهدف هو حساب البوت", target_id, chat_id)
        return None
    try:
        target_perms = await client.get_permissions(chat_id, target_id)
        if target_perms.is_admin or target_perms.is_creator:
            logger.info("warn-limit: تخطّي %s في %s — الهدف مشرف", target_id, chat_id)
            await client.send_message(
                BOTLOG_CHATID,
                f"**⎉╎تحذيرات:** تخطّيت {action} `{target_id}` لأنه مشرف في الدردشة ✅",
            )
            return None
    except Exception as e:
        logger.warning("warn-limit: تعذّر فحص صلاحيات %s في %s: %s", target_id, chat_id, e)
    try:
        my_perms = await client.get_permissions(chat_id, me.uid)
        if not my_perms.ban_users:
            logger.warning("warn-limit: لا توجد صلاحية حظر في %s", chat_id)
            await client.send_message(
                BOTLOG_CHATID,
                f"**⎉╎تحذيرات:** لا أملك صلاحية {action} في هذه المجموعة — لم يُنفَّذ الإجراء ⛔️",
            )
            return None
    except Exception as e:
        logger.error("warn-limit: تعذّر فحص صلاحياتي في %s: %s", chat_id, e)
        await client.send_message(
            BOTLOG_CHATID,
            f"**⎉╎تحذيرات:** تعذّر التحقق من الصلاحيات:\n`{e}`",
        )
        return None
    try:
        if soft_warn:
            await client.kick_participant(chat_id, target_id)
        else:
            await client(EditBannedRequest(chat_id, target_id, BANNED_RIGHTS))
    except Exception as e:
        logger.error("warn-limit: فشل %s لـ %s في %s: %s", action, target_id, chat_id, e)
        await client.send_message(
            BOTLOG_CHATID,
            f"**⎉╎تحذيرات:** فشل {action} المستخدم `{target_id}`:\n`{e}`",
        )
        return None
    logger.info(
        "warn-limit: تم %s لـ %s في %s بعد %s تحذيرات",
        action,
        target_id,
        chat_id,
        limit,
    )
    await client.send_message(
        BOTLOG_CHATID,
        f"**⎉╎تحذيرات:** تم {action} `{target_id}` بعد تجاوز {limit} تحذيرات ✓",
    )
    return action


@zedub.zed_cmd(incoming=True, groups_only=True)
async def on_new_message(event):
    name = event.raw_text
    snips = spl.get_chat_blacklist(event.chat_id)
    zthonadmin = await is_admin(event.client, event.chat_id, event.client.uid)
    if not zthonadmin:
        return
    for snip in snips:
        pattern = f"( |^|[^\\w]){re.escape(snip)}( |$|[^\\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            try:
                await event.delete()
            except Exception:
                await event.client.send_message(
                    BOTLOG_CHATID,
                    f"**⎉╎عـذراً عـزيـزي مـالك البـوت\n⎉╎ليست لدي صلاحية الحذف في** {get_display_name(await event.get_chat())}.\n**⎉╎لذا لن يتم إزالة الكلمات الممنوعـه في تلك الدردشـه ؟!**",
                )
                # لا نحذف قائمة المنع نفسها عند فشل الحذف —
                # بيانات المالك تبقى محفوظة ولا نلغي التنبيه فقط.
            break


@zedub.zed_cmd(
    pattern=r"منع(?:\s|$)([\s\S]*)",
    require_admin=True,
)
async def _(event):
    text = event.pattern_match.group(1)
    to_blacklist = list({trigger.strip() for trigger in text.split("\n") if trigger.strip()})

    for trigger in to_blacklist:
        spl.add_to_blacklist(event.chat_id, trigger.lower())
    await edit_or_reply(
        event,
        f"**⎉╎تم اضافة (** {len(to_blacklist)} **)**\n**⎉╎الى قائمة الكلمـات الممنوعـه هنـا .. بنجـاح ✓**",
    )


@zedub.zed_cmd(
    pattern=r"الغاء منع(?:\s|$)([\s\S]*)",
    require_admin=True,
)
async def _(event):
    text = event.pattern_match.group(1)
    to_unblacklist = list({trigger.strip() for trigger in text.split("\n") if trigger.strip()})
    successful = sum(bool(spl.rm_from_blacklist(event.chat_id, trigger.lower())) for trigger in to_unblacklist)
    await edit_or_reply(
        event,
        f"**⎉╎تم حذف (** {successful} / {len(to_unblacklist)} **(**\n**⎉╎من قائمة الكلمـات الممنوعـه هنـا .. بنجـاح ✓**",
    )


@zedub.zed_cmd(
    pattern="قائمة المنع$",
    require_admin=True,
)
async def _(event):
    all_blacklisted = spl.get_chat_blacklist(event.chat_id)
    OUT_STR = "**⎉╎قائمة الكلمـات الممنوعـه هنـا هـي :\n**"
    if len(all_blacklisted) > 0:
        for trigger in all_blacklisted:
            OUT_STR += f"- {trigger} \n"
    else:
        OUT_STR = "**⎉╎لم يتم اضافة كلمـات ممنوعـة هنـا بعـد ؟!**"
    await edit_or_reply(event, OUT_STR)


@zedub.zed_cmd(
    pattern="قائمه المنع$",
    require_admin=True,
)
async def _(event):
    all_blacklisted = spl.get_chat_blacklist(event.chat_id)
    OUT_STR = "**⎉╎قائمة الكلمـات الممنوعـه هنـا هـي :\n**"
    if len(all_blacklisted) > 0:
        for trigger in all_blacklisted:
            OUT_STR += f"- {trigger} \n"
    else:
        OUT_STR = "**⎉╎لم يتم اضافة كلمـات ممنوعـة هنـا بعـد ؟!**"
    await edit_or_reply(event, OUT_STR)


# ================================================================================================ #
# =========================================التحذيرات================================================= #
# ================================================================================================ #


@zedub.zed_cmd(
    pattern=r"تحذير(?:\s|$)([\s\S]*)",
    require_admin=True,
)
async def _(event):
    warn_reason = event.pattern_match.group(1)
    if not warn_reason:
        warn_reason = "**⪼ لايوجـد سبب 🗒**"
    reply_message = await event.get_reply_message()
    if not reply_message:
        return await edit_delete(event, "**⎉╎بالـرد ع المستخـدم لـ تحذيـره ☻**")
    if not reply_message.sender_id:
        return await edit_delete(event, "**⎉╎لا يمكن تحذيـر هذا المستخـدم !؟**")
    limit, soft_warn = sql.get_warn_setting(event.chat_id)
    num_warns, reasons = sql.warn_user(reply_message.sender_id, event.chat_id, warn_reason)
    if num_warns >= limit:
        sql.reset_warns(reply_message.sender_id, event.chat_id)
        action = await _apply_warn_punishment(event, reply_message.sender_id, soft_warn, limit)
        if action:
            reply = f"**⎉╎بسبب تخطي التحذيـرات الـ {limit} ،**\n**⎉╎تم {action} المستخـدم! ✅**"
        else:
            reply = (f"**⎉╎بسبب تخطي التحذيـرات الـ {limit} ،**\n**⎉╎تعذّر تنفيذ الإجراء — راجـع سجـل الأوامر 🗂**")
    else:
        reply = f"**⎉╎[ المستخدم 👤](tg://user?id={reply_message.sender_id}) **\n**⎉╎لديـه {num_warns}/{limit} تحذيـرات .. احـذر!**"
        if warn_reason:
            reply += f"\n**⎉╎سبب التحذير الأخير **\n{html.escape(warn_reason)}"
    await edit_or_reply(event, reply)


@zedub.zed_cmd(pattern="التحذيرات", require_admin=True)
async def _(event):
    reply_message = await event.get_reply_message()
    if not reply_message:
        return await edit_delete(event, "**⎉╎بالـرد ع المستخـدم للحصول ع تحذيراتـه ☻**")
    result = sql.get_warns(reply_message.sender_id, event.chat_id)
    if not result or result[0] == 0:
        return await edit_or_reply(event, "**⎉╎هـذا المستخـدم ليس لديه أي تحذيـرات! ツ**")
    num_warns, reasons = result
    limit, soft_warn = sql.get_warn_setting(event.chat_id)
    if not reasons:
        return await edit_or_reply(
            event,
            f"**⎉╎[ المستخدم 👤](tg://user?id={reply_message.sender_id}) **\n**⎉╎لديـه {num_warns}/{limit} تحذيـرات ، **\n**⎉╎لكـن لا توجـد اسباب ؟!**",
        )

    text = f"**⎉╎[ المستخـدم 👤](tg://user?id={reply_message.sender_id}) **\n**⎉╎لديـه {num_warns}/{limit} تحذيـرات ، **\n**⎉╎للأسباب : ↶**"
    text += "\n"
    text += html.escape(reasons)
    await edit_or_reply(event, text)


@zedub.zed_cmd(
    pattern="حذف التحذيرات(?: |$)(.*)",
    require_admin=True,
)
async def _(event):
    reply_message = await event.get_reply_message()
    if not reply_message:
        return await edit_delete(event, "**⎉╎بالـرد ع المستخـدم لـ صفـر تحذيراتـه ☻**")
    if not reply_message.sender_id:
        return await edit_delete(event, "**⎉╎لا يمكن صفـر تحذيرات هذا المستخـدم !؟**")
    sql.reset_warns(reply_message.sender_id, event.chat_id)
    await edit_or_reply(event, "**⎉╎تم إعـادة ضبط التحذيـرات! .. بنجـاح**")
