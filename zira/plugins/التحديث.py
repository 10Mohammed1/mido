import asyncio
import contextlib
import os
import sys
import time
from asyncio.exceptions import CancelledError

import heroku3
import urllib3
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from ..Config import Config
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..sql_helper.global_collection import (
    add_to_collectionlist,
    del_keyword_collectionlist,
    get_collectionlist_items,
)
from . import HEROKU_APP, UPSTREAM_REPO_URL, zedub

plugin_category = "الادوات"
cmdhd = Config.COMMAND_HAND_LER
ENV = bool(os.environ.get("ENV", False))
LOGS = logging.getLogger(__name__)
# -- Constants -- #

HEROKU_APP_NAME = Config.HEROKU_APP_NAME or None
HEROKU_API_KEY = Config.HEROKU_API_KEY or None
Heroku = heroku3.from_key(Config.HEROKU_API_KEY)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Project root derived from THIS file (zira/plugins → root).  Never a
# hardcoded path like /app, so updates work on any host (VPS/Docker/Windows).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
requirements_path = os.path.join(PROJECT_ROOT, "requirements.txt")
# File that records the name of the last safety-net tag (for التراجع).
BACKUP_REF_FILE = os.path.join(PROJECT_ROOT, ".update_backup_ref")

UPSTREAM_ERROR_PREFIX = "`Oops.. Updater cannot continue due to some problems occured`\n\n**LOGTRACE:**\n"


def _configured_branch():
    return getattr(Config, "UPSTREAM_REPO_BRANCH", None) or "main"


def _create_backup_tag(repo):
    """Local annotated tag created BEFORE anything changes."""
    tag_name = "backup/auto-update-" + time.strftime("%Y%m%d-%H%M%S")
    repo.create_tag(tag_name, message="automatic backup before source update")
    try:
        with open(BACKUP_REF_FILE, "w") as f:
            f.write(tag_name)
    except OSError as e:
        LOGS.warning("could not record backup ref: %s", e)
    return tag_name


def _ensure_upstream_remote(repo):
    """Return the 'upstream' remote pointed at UPSTREAM_REPO_URL."""
    if "upstream" in [r.name for r in repo.remotes]:
        remote = repo.remote("upstream")
        if list(remote.urls) != [UPSTREAM_REPO_URL]:
            remote.set_url(UPSTREAM_REPO_URL)
        return remote
    return repo.create_remote("upstream", UPSTREAM_REPO_URL)


def _fetch_upstream(repo, ups_rem):
    """Fetch the configured upstream branch, falling back to known names."""
    candidates = [_configured_branch(), "main", "master"]
    with contextlib.suppress(Exception):
        candidates.append(repo.active_branch.name)
    seen, last_err = set(), None
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            ups_rem.fetch(candidate)
            return candidate
        except GitCommandError as e:
            last_err = e
    raise last_err or GitCommandError("no upstream branch could be fetched")


async def gen_chlog(repo, diff):
    d_form = "%d/%m/%y"
    return "".join(
        f"  • {c.summary} ({c.committed_datetime.strftime(d_form)}) <{c.author}>\n" for c in repo.iter_commits(diff)
    )


async def update_requirements():
    """Install requirements.txt with exec (no shell) and return the exit code."""
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            requirements_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=1800)
    except Exception as e:
        LOGS.error("requirements update failed to start: %s", e)
        return 1
    if process.returncode != 0:
        LOGS.error(
            "pip install failed (%s): %s",
            process.returncode,
            (stderr or b"")[-500:].decode(errors="replace"),
        )
    return process.returncode


async def safe_update(event):
    """The single update path: backup → fetch → ff-merge → deps → restart.

    * Never runs `git reset --hard` and never touches local modifications:
      a fast-forward merge simply refuses to proceed when they conflict.
    * A `backup/auto-update-*` tag is created first, and `.تراجع التحديث`
      rolls back to it with `git reset --keep`.
    """
    head = await edit_or_reply(
        event,
        "ᯓ 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - تحـديثـات السـورس\n**•─────────────────•**\n\n**⪼ جـارِ تحـديـث السـورس .. انتظـر 🌐**",
        link_preview=False,
    )
    # 1) open the repository
    try:
        repo = Repo(PROJECT_ROOT)
    except (NoSuchPathError, InvalidGitRepositoryError):
        return await edit_delete(
            head,
            "⛔ **هذا المجلد ليس مستودع git:**\n`" + PROJECT_ROOT + "`\nلم يتغيّر أي شيء.",
        )
    # 2) safety-net tag BEFORE touching anything
    try:
        tag_name = await asyncio.to_thread(_create_backup_tag, repo)
    except Exception as e:
        LOGS.error("backup tag failed: %s", e)
        return await edit_delete(head, f"⛔ **تعذّرت النسخة الاحتياطية — أُلغي التحديث.**\n`{e}`")
    # 3) fetch upstream
    try:
        ups_rem = await asyncio.to_thread(_ensure_upstream_remote, repo)
        branch = await asyncio.to_thread(_fetch_upstream, repo, ups_rem)
    except Exception as e:
        return await edit_delete(
            head,
            "⛔ **فشل جلب التحديث:**\n"
            f"**المصدر:** `{UPSTREAM_REPO_URL}`\n"
            f"**الفرع:** `{_configured_branch()}`\n`{e}`\n\n"
            f"**النسخة الاحتياطية:** `{tag_name}`",
        )
    # 4) what is new?
    try:
        ac_br = repo.active_branch.name
        changelog = (await gen_chlog(repo, f"{ac_br}..FETCH_HEAD")).strip()
    except Exception:
        ac_br = "HEAD"
        changelog = ""
    preview = changelog[:2500] + ("\n…" if len(changelog) > 2500 else "")
    await head.edit(
        "ᯓ 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - تحـديثـات السـورس\n**•─────────────────•**\n\n"
        f"**⪼ الفـرع:** `{branch}` ← `{UPSTREAM_REPO_URL}`\n"
        f"**⪼ نسخـة احـتياطية:** `{tag_name}`\n\n"
        + (f"**التحديثـات:**\n```\n{preview}\n```\n\n" if preview else "")
        + "**⪼ جـارِ التطبيـق ..⎋**",
        link_preview=False,
    )
    # 5) fast-forward ONLY – refuses when local changes would be overwritten
    try:
        await asyncio.to_thread(repo.git.merge, "--ff-only", "FETCH_HEAD")
    except GitCommandError as e:
        return await edit_delete(
            head,
            "⚠️ **تعذّر التحديث التلقائي — لم يتغيّر شيء وتعديلاتك محفوظة:**\n"
            f"`{e}`\n\n"
            f"**للتراجع عن النسخة الاحتياطية:** `{cmdhd}تراجع التحديث`",
        )
    # 6) dependencies
    rc = await update_requirements()
    deps = "✅ **الاعتمادات: مُحدَّثة**" if rc == 0 else f"⚠️ **تعذّر تثبيت الاعتمادات (رمز {rc}) — راجع السجلات**"
    # 7) deploy (Heroku) or restart in place
    if ENV and HEROKU_API_KEY and HEROKU_APP_NAME:
        return await deploy(head, repo, ups_rem, ac_br, UPSTREAM_ERROR_PREFIX, deps)
    await head.edit(
        "ᯓ 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - تحـديثـات السـورس\n**•─────────────────•**\n\n"
        f"**✅ تـم تحـديث السـورس إلى:** `{tag_name}`\n{deps}\n\n"
        "**⪼ جـارِ إعـادة التشغيـل 🌐**",
        link_preview=False,
    )
    await asyncio.sleep(1)
    try:
        await event.client.reload(head)
    except Exception as e:
        LOGS.error("reload after update failed: %s", e)
        await edit_or_reply(head, f"**تم التحديث، لكن أُعيد التشغيل يدويًا.**\n`{e}`")


async def deploy(event, repo, ups_rem, ac_br, txt, deps=""):
    if HEROKU_API_KEY is None:
        return await event.edit(
            "ᯓ 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - تحـديثـات السـورس\n **•─────────────────•**\n"
            "** ⪼ لم تقـم بوضـع مربـع فـار HEROKU_API_KEY اثنـاء التنصيب وهـذا خطـأ .. "
            "قم بضبـط المتغيـر أولاً لتحديث بوت Mido ..؟!**",
            link_preview=False,
        )
    heroku = heroku3.from_key(HEROKU_API_KEY)
    heroku_applications = heroku.apps()
    if HEROKU_APP_NAME is None:
        await event.edit(
            "ᯓ 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - تحـديثـات السـورس\n **•─────────────────•**\n"
            "** ⪼ لم تقـم بوضـع مربـع فـار HEROKU_APP_NAME اثنـاء التنصيب وهـذا خطـأ .. "
            "قم بضبـط المتغيـر أولاً لتحديث بوت Mido ..؟!**",
            link_preview=False,
        )
        repo.__del__()
        return
    heroku_app = next(
        (app for app in heroku_applications if app.name == HEROKU_APP_NAME),
        None,
    )

    if heroku_app is None:
        await event.edit(f"{txt}\n**- بيانات اعتماد هيروكو غير صالحة لتنصيب تحديث Mido**")
        return repo.__del__()
    sandy = await event.edit(
        "ᯓ 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - تحـديثـات السـورس\n**•─────────────────•**\n\n"
        "**✾╎جـارِ . . تنصـيب التحـديث الجـذري ⎌**\n"
        "**✾╎يـرجى الانتظـار حتى تنتـهي العمليـة ⎋**\n"
        "**✾╎عادة ما يستغرق هـذا التحديث من 5 - 4 دقائـق 📟**"
    )
    try:
        ulist = get_collectionlist_items()
        for i in ulist:
            if i == "restart_update":
                del_keyword_collectionlist("restart_update")
    except Exception as e:
        LOGS.error(e)
    try:
        add_to_collectionlist("restart_update", [sandy.chat_id, sandy.id])
    except Exception as e:
        LOGS.error(e)
    # `git reset --hard` is intentionally absent: the fast-forward merge in
    # safe_update() already updated the tree without touching local edits.
    heroku_git_url = heroku_app.git_url.replace("https://", f"https://api:{HEROKU_API_KEY}@")

    if "heroku" in repo.remotes:
        remote = repo.remote("heroku")
        remote.set_url(heroku_git_url)
    else:
        remote = repo.create_remote("heroku", heroku_git_url)
    try:
        remote.push(refspec="HEAD:refs/heads/lite", force=True)
    except Exception as error:
        await event.edit(f"{txt}\n**Error log:**\n`{error}`")
        return repo.__del__()
    build_status = heroku_app.builds(order_by="created_at", sort="desc")[0]
    if build_status.status == "failed":
        return await edit_delete(event, "`Build failed!\nCancelled or there were some errors...`")
    try:
        remote.push("lite:main", force=True)
    except Exception as error:
        await event.edit(f"{txt}\n**Here is the error log:**\n`{error}`")
        return repo.__del__()
    await event.edit(
        "ᯓ 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - تحـديثـات السـورس\n**•─────────────────•**\n\n"
        f"**•⎆┊ تـم تحـديث السـورس ✅**\n{deps}\n"
        "**•⎆┊سـوف يتـم إعـادة تشغيـل تطبيـق هيروكو 🌐 **"
    )
    with contextlib.suppress(CancelledError):
        await event.client.disconnect()
        if HEROKU_APP is not None:
            HEROKU_APP.restart()


@zedub.zed_cmd(
    pattern="(تحديث البوت|تحديث الان)$",
    command=("تحديث البوت", plugin_category),
    info={
        "header": "تحديث آمن لسورس Mido مع نسخة احتياطية قابلة للتراجع",
        "description": "جلب آخر التحديثات من المستودع، دمج بدون فقدان أي تعديلات محلية، ثم تثبيت الاعتماديات وإعادة التشغيل.",
        "note": f"يتم عمل وسم احتياطي (backup/auto-update-*) قبل التحديث. للتراجع استخدم `{cmdhd}تراجع التحديث`.",
        "usage": [
            "{tr}تحديث البوت",
            "{tr}تحديث الان",
        ],
    },
)
async def upstream(event):
    if ENV and (HEROKU_API_KEY is None or HEROKU_APP_NAME is None):
        return await edit_or_reply(
            event,
            "**- بيانات اعتماد تنصيبك غير صالحة لتنصيب تحديث Mido ❕❌**\n"
            "**- يجب تعييـن قيـم مربعـات الفارات التالية يدوياً من حساب هيروكـو 🛂**\n\n\n"
            "**- مربـع مفتـاح هيروكـو :** HEROKU_API_KEY\n"
            "**- مربـع اسـم التطبيـق :** HEROKU_APP_NAME",
        )
    await safe_update(event)


@zedub.zed_cmd(
    pattern="تراجع التحديث$",
    command=("تراجع التحديث", plugin_category),
    info={
        "header": "الرجوع إلى النسخة الاحتياطية التي قبل آخر تحديث",
        "description": "يستخدم git reset --keep فلا يُحذف أي تعديل تم بعد التحديث، ثم يعيد تثبيت الاعتماديات.",
        "usage": "{tr}تراجع التحديث",
    },
)
async def rollback_update(event):
    head = await edit_or_reply(
        event,
        "ᯓ 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - تحـديثـات السـورس\n**•─────────────────•**\n\n**⪼ جـارِ التراجـع إلـى النسخة السـابقة ..⎋**",
        link_preview=False,
    )
    try:
        with open(BACKUP_REF_FILE) as f:
            tag_name = f.read().strip()
    except OSError:
        return await edit_delete(head, "لا توجد نسخة احتياطية مسجّلة (لم يتم تحديث بعد).")
    try:
        repo = Repo(PROJECT_ROOT)
    except Exception as e:
        return await edit_delete(head, f"⛔ `{e}`")
    if tag_name not in repo.tags:
        return await edit_delete(head, f"⛔ وسوم النسخة الاحتياطية غير موجودة: `{tag_name}`")
    try:
        # --keep: aborts instead of destroying any change made afterwards.
        await asyncio.to_thread(repo.git.reset, "--keep", tag_name)
    except GitCommandError as e:
        return await edit_delete(
            head,
            f"⛔ **تعذّر التراجع لوجود تعارض مع تعديلاتك — لم يتغيّر شيء:**\n`{e}`",
        )
    rc = await update_requirements()
    deps = "✅ **الاعتمادات: مُسترجَعة**" if rc == 0 else f"⚠️ **تعذّر تثبيت الاعتمادات (رمز {rc}) — راجع السجلات**"
    await head.edit(
        "ᯓ 𝗦𝗼𝘂𝗿𝗰𝗲 Mido - تحـديثـات السـورس\n**•─────────────────•**\n\n"
        f"**✅ تـم التراجـع إلـى:** `{tag_name}`\n{deps}\n\n"
        "**⪼ جـارِ إعـادة التشغيـل 🌐**",
        link_preview=False,
    )
    await asyncio.sleep(1)
    try:
        await event.client.reload(head)
    except Exception as e:
        LOGS.error("reload after rollback failed: %s", e)
        await edit_or_reply(head, f"**تم التراجع، لكن أُعد التشغيل يدويًا.**\n`{e}`")
