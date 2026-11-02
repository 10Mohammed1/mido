import logging
import sys
from subprocess import PIPE, Popen

LOGS = logging.getLogger("Mido")


def install_pip(pipfile):
    """يثبّت حزمة عبر pip — للنداء الصريح فقط (أمر من المالك).

    لا يُستدعى تلقائيًا أثناء الإقلاع. يرفض الخيارات (تبدأ بـ -) وروابط
    git/url لمنع حقن وسائط pip من نصوص غير موثوقة.
    """
    if not isinstance(pipfile, str) or not pipfile.strip():
        LOGS.warning("install_pip: اسم حزمة غير صالح: %r", pipfile)
        return b""
    pkg = pipfile.strip()
    if pkg.startswith("-") or "://" in pkg or "+" in pkg:
        LOGS.warning("install_pip: رفض طلب غير موثوق: %r", pkg)
        return b""
    # use the interpreter that is actually running the bot - a bare `pip`
    # binary does not exist on every system (only `pip3`).
    LOGS.info("install_pip: تثبيت %s (طلب صريح)", pkg)
    pip_cmd = [sys.executable, "-m", "pip", "install", pkg]
    process = Popen(pip_cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if process.returncode:
        LOGS.error(
            "install_pip: فشل تثبيت %s: %s",
            pkg,
            stderr.decode(errors="replace")[:300],
        )
    return stdout
