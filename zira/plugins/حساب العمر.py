#Mido

from datetime import datetime

from zira import zedub
from ..core.managers import edit_delete, edit_or_reply


@zedub.zed_cmd(pattern=r"حساب العمر(?:\s|$)([\s\S]*)")
async def _(event):
    yar = event.text[12:]
    if not yar:
       return await edit_or_reply(event, "**✾╎استخـدم الامـر كالتالـي .. حساب العمر + السنـه**")
    try:
        yar = int(yar.strip())
    except ValueError:
        return await edit_or_reply(
            event, "**✾╎ارسـل السـنـه بـ ارقـام فقـط .. مثـال :** `.حساب العمر 2000`"
        )
    YearNow = datetime.now().year
    MyAge = YearNow - yar
    await edit_or_reply(event, "**🚹╎عمرك هـو :**  {}".format(MyAge))
