# ported from uniborg by @spechide
import asyncio
import io
import math
import os
import re
import time
from datetime import datetime

from . import zedub
from ..core.logger import logging

from ..Config import Config
from ..core.managers import edit_delete, edit_or_reply
from ..helpers import (
    _zedtools,
    _zedutils,
    fileinfo,
    humanbytes,
    media_type,
    progress,
    readable_time,
    reply_id,
    time_formatter,
)

plugin_category = "الادوات"


thumb_image_path = os.path.join(Config.TMP_DOWNLOAD_DIRECTORY, "thumb_image.jpg")
FF_MPEG_DOWN_LOAD_MEDIA_PATH = os.path.join(Config.TMP_DOWNLOAD_DIRECTORY, "zedzthon.media.ffmpeg")
FINISHED_PROGRESS_STR = Config.FINISHED_PROGRESS_STR
UN_FINISHED_PROGRESS_STR = Config.UNFINISHED_PROGRESS_STR
LOGGER = logging.getLogger(__name__)

# Safety nets: never let a stuck ffmpeg hang the bot forever.
FFMPEG_TIMEOUT = 60 * 60  # seconds – full compression
TRIM_TIMEOUT = 15 * 60  # seconds – trim / screenshot


async def convert_video(video_file, output_directory, crf, total_time, bot, message):
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = os.path.join(output_directory, str(round(time.time())) + ".mp4")
    # ffmpeg WRITES progress here and we must READ from the same path.
    progress_path = os.path.join(output_directory, "progress.txt")
    with open(progress_path, "w"):
        pass
    COMPRESSION_START_TIME = time.time()
    try:
        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "quiet",
            "-progress",
            progress_path,
            "-i",
            str(video_file),
            "-preset",
            "ultrafast",
            "-vcodec",
            "libx265",
            "-crf",
            str(crf),
            "-c:a",
            "copy",
            str(out_put_file_name),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        LOGGER.error("ffmpeg is not installed / not found in PATH")
        return None
    except Exception as e:
        LOGGER.error("failed to start ffmpeg: %s", e)
        return None
    LOGGER.info("ffmpeg_process: " + str(process.pid))

    total_time = total_time or 0
    # communicate() drains BOTH pipes concurrently so ffmpeg can never block
    # on a full pipe; the loop only watches completion and enforces timeout.
    communicate_task = asyncio.create_task(process.communicate())
    try:
        while not communicate_task.done():
            if time.time() - COMPRESSION_START_TIME > FFMPEG_TIMEOUT:
                LOGGER.error("ffmpeg timed out after %ss, killing it", FFMPEG_TIMEOUT)
                process.kill()
                break
            await asyncio.sleep(3)
            try:
                with open(progress_path, "r") as file:
                    text = file.read()
            except OSError:
                continue  # progress file not written yet
            time_in_us = re.findall(r"out_time_(?:ms|us)=(\d+)", text)
            speed = re.findall(r"speed=(\d+\.?\d*)", text)
            speed = speed[-1] if speed else "1"
            time_in_us = int(time_in_us[-1]) if time_in_us else 0
            elapsed_time = time_in_us / 1000000
            difference = 0
            if total_time > 0:
                percentage = math.floor(elapsed_time * 100 / total_time)
                percentage = min(100, max(0, percentage))
                try:
                    difference = math.floor((total_time - elapsed_time) / float(speed))
                except (ValueError, ZeroDivisionError):
                    difference = 0
            else:
                percentage = 0
            ETA = time_formatter(difference) if difference > 0 else "-"
            finished = min(10, max(0, math.floor(percentage / 10)))
            progress_str = "📊 **Progress :** {0}%\n[{1}{2}]".format(
                percentage,
                "".join([FINISHED_PROGRESS_STR for _ in range(finished)]),
                "".join([UN_FINISHED_PROGRESS_STR for _ in range(10 - finished)]),
            )
            stats = f"📦️ **Compressing CRF-{crf}**\n\n⏰️ **ETA :** {ETA}\n\n{progress_str}\n"
            try:
                await message.edit(text=stats)
            except Exception:
                pass
    finally:
        # Reap the process (already finished, killed, or about to be killed).
        _, stderr = await communicate_task
    if process.returncode != 0:
        err = (stderr or b"")[-400:].decode(errors="replace")
        LOGGER.error("ffmpeg exited with code %s: %s", process.returncode, err)
        return None
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    return None


async def cult_small_video(video_file, output_directory, start_time, end_time, out_put_file_name=None):
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = out_put_file_name or os.path.join(output_directory, f"{round(time.time())}.mp4")
    try:
        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-i",
            str(video_file),
            "-ss",
            str(start_time),
            "-to",
            str(end_time),
            "-async",
            "1",
            "-strict",
            "-2",
            str(out_put_file_name),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        LOGGER.error("ffmpeg is not installed / not found in PATH")
        return None
    except Exception as e:
        LOGGER.error("failed to start ffmpeg: %s", e)
        return None
    try:
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=TRIM_TIMEOUT)
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        LOGGER.error("ffmpeg trim timed out after %ss, killing it", TRIM_TIMEOUT)
        return None
    if process.returncode != 0:
        err = (stderr or b"")[-400:].decode(errors="replace")
        LOGGER.error("ffmpeg trim exited with code %s: %s", process.returncode, err)
        return None
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    return None


@zedub.zed_cmd(
    pattern=r"(|ا)ضغط(?:\s|$)([\s\S]*)",
    command=("ضغط", plugin_category),
    info={
        "header": "Compress the video file.",
        "description": "Will compress the replied video, if not replied to video it will check any video saved by .ffmpegsave or not.",
        "flags": {
            "ا": "To Force file the compressed video.",
        },
        "note": "For quality of compress choose CRF value [ 0 - 51 ]\nHigher crf value = less video size = low on quality.\nIf no crf given it will use default value 23.",
        "usage": [
            "{tr}ضغط < 0 - 51 >",
            "{tr}اضغط < 0 - 51 >",
        ],
        "examples": [
            "{tr}ضغط",
            "{tr}اضغط",
            "{tr}ضغط 35",
            "{tr}اضغط 35",
        ],
    },
)
async def ffmpeg_compress(event):
    "Compress the video file."
    crf = event.pattern_match.group(2)
    reply_to_id = await reply_id(event)
    cmd = event.pattern_match.group(1).lower()
    reply_message = await event.get_reply_message()
    start = datetime.now()
    if not crf or not crf.isdigit() or not 0 <= int(crf) <= 51:
        crf = "23"
    dlpath = os.path.join(Config.TMP_DOWNLOAD_DIRECTORY, "Mido.media.ffmpeg")
    delete = False
    zedevent = None
    if not reply_message or not reply_message.media:
        if os.path.exists(FF_MPEG_DOWN_LOAD_MEDIA_PATH):
            media = (await fileinfo(FF_MPEG_DOWN_LOAD_MEDIA_PATH))["type"]
            if media not in ["Video"]:
                return await edit_delete(event, "**- الامـر يدعـم فقـط ملفـات الفيـديـو . . .**")
            dlpath = FF_MPEG_DOWN_LOAD_MEDIA_PATH
            zedevent = await edit_or_reply(event, "**- جـارِ ضغـط ملـف الفيـديـو . . .**")
            delete = False
        else:
            return await edit_delete(event, "**- بالـرد ع فيـديـو . . .**")
    else:
        media = media_type(reply_message)
        if media not in ["Video", "Round Video", "Gif"]:
            return await edit_delete(event, "**- الامـر يدعـم فقـط ملفـات الفيـديـو . . .**")
        zedevent = await edit_or_reply(event, "**- جـارِ حفـظ المـلف . . .**")
        try:
            c_time = time.time()
            dl = io.FileIO(dlpath, "a")
            await event.client.fast_download_file(
                location=reply_message.document,
                out=dl,
                progress_callback=lambda d, t: asyncio.get_running_loop().create_task(
                    progress(d, t, zedevent, c_time, "**- جـاِ التنـزيـل . . .**")
                ),
            )
            dl.close()
        except Exception as e:
            return await edit_or_reply(zedevent, f"**- خطـأ :**\n`{e}`")
        else:
            await edit_or_reply(zedevent, "**- جـارِ ضغـط ملـف الفيـديـو . . .**")
            delete = True
    if not os.path.exists(dlpath):
        return await edit_delete(zedevent, "**- لم يتم العثـر ع ملف فيديـو . . .**")
    old = await fileinfo(dlpath)
    os.makedirs("./temp", exist_ok=True)
    cstart = datetime.now()
    compress = await convert_video(dlpath, "./temp", crf, old.get("duration"), zedub, zedevent)
    cend = datetime.now()
    cms = (cend - cstart).seconds
    if delete:
        os.remove(dlpath)
    if compress:
        new = await fileinfo(compress)
        osize = old["size"]
        nsize = new["size"]
        cap = f"**- الحجـم السـابق :** `{humanbytes(osize)}`\n**- الحجـم الجـديـد :** `{humanbytes(nsize)}`\n**- تم ضغـط :** `{int(100 - (nsize / osize * 100)) if osize else 0}%`\n\n**- الوقـت المستغـرق :-**\n**- الضغـط : **`{time_formatter(cms)}`"
        if cmd == "ا":
            try:
                c_time = time.time()
                catt = await event.client.send_file(
                    event.chat_id,
                    compress,
                    thumb=thumb_image_path,
                    caption=cap,
                    force_document=True,
                    supports_streaming=True,
                    allow_cache=False,
                    reply_to=reply_to_id,
                    progress_callback=lambda d, t: asyncio.get_running_loop().create_task(
                        progress(d, t, zedevent, c_time, "**- جـارِ الرفـع . . .**")
                    ),
                )
                os.remove(compress)
            except Exception as e:
                return await edit_delete(zedevent, f"**- خطـأ : **`{e}`")
        else:
            thumb = await _zedtools.take_screen_shot(compress, "00:01")
            try:
                c_time = time.time()
                catt = await event.client.send_file(
                    event.chat_id,
                    compress,
                    caption=cap,
                    thumb=thumb,
                    force_document=False,
                    supports_streaming=True,
                    allow_cache=False,
                    reply_to=reply_to_id,
                    progress_callback=lambda d, t: asyncio.get_running_loop().create_task(
                        progress(d, t, zedevent, c_time, "Trying to upload")
                    ),
                )
                os.remove(compress)
            except Exception as e:
                return await edit_delete(zedevent, f"**- خطـأ : **`{e}`")
    else:
        return await edit_delete(zedevent, "**ERROR :: Unable to Compress**")
    await zedevent.delete()
    end = datetime.now()
    ms = (end - start).seconds
    cap += f"\n**- الاجمـالـي :** `{time_formatter(ms)}`"
    await edit_or_reply(catt, cap)


@zedub.zed_cmd(
    pattern=r"ffmpegsave(?:\s|$)([\s\S]*)",
    command=("ffmpegsave", plugin_category),
    info={
        "header": "Saves the media file in bot to trim mutliple times",
        "description": "Will download the replied media into the bot so that you an trim it as your needs.",
        "usage": "{tr}ffmpegsave <reply>",
    },
)
async def ff_mpeg_save_cmd(event):
    "Saves the media file in bot to trim mutliple times"
    mpath = event.pattern_match.group(1)
    if not os.path.exists(FF_MPEG_DOWN_LOAD_MEDIA_PATH):
        if mpath and os.path.exists(mpath):
            media = (await fileinfo(mpath))["type"]
            if media not in ["Video", "Audio"]:
                return await edit_delete(event, "`Only media files are supported`", 5)
            await _zedutils.runcmd(f"cp -r {mpath} {FF_MPEG_DOWN_LOAD_MEDIA_PATH}")
            return await edit_or_reply(event, f"Saved file to `{FF_MPEG_DOWN_LOAD_MEDIA_PATH}`")
        reply_message = await event.get_reply_message()
        if reply_message:
            start = datetime.now()
            media = media_type(reply_message)
            if media not in ["Video", "Audio", "Voice", "Round Video", "Gif"]:
                return await edit_delete(event, "`Only media files are supported`", 5)
            zedevent = await edit_or_reply(event, "`Saving the file...`")
            try:
                c_time = time.time()
                dl = io.FileIO(FF_MPEG_DOWN_LOAD_MEDIA_PATH, "a")
                await event.client.fast_download_file(
                    location=reply_message.document,
                    out=dl,
                    progress_callback=lambda d, t: asyncio.get_running_loop().create_task(
                        progress(d, t, zedevent, c_time, "trying to download")
                    ),
                )
                dl.close()
            except Exception as e:
                await edit_or_reply(zedevent, f"**Error:**\n`{e}`")
            else:
                end = datetime.now()
                ms = (end - start).seconds
                await edit_or_reply(
                    zedevent,
                    f"Saved file to `{FF_MPEG_DOWN_LOAD_MEDIA_PATH}` in `{ms}` seconds.",
                )
        else:
            await edit_delete(event, "`Reply to a any media file`")
    else:
        await edit_delete(
            event,
            "A media file already exists in path. Please remove the media and try again!\n`.ffmpegclear`",
        )


@zedub.zed_cmd(
    pattern=r"vtrim(?:\s|$)([\s\S]*)",
    command=("vtrim", plugin_category),
    info={
        "header": "Trims the saved media with specific given time internval and outputs as video if it is video",
        "description": "Will trim the saved media with given time interval.",
        "note": "if you haven't mentioned time interval and just time then will send screenshot at that location.",
        "usage": "{tr}vtrim <time interval>",
        "examples": "{tr}vtrim 00:00 00:10",
    },
)
async def ff_mpeg_vtrim_cmd(event):
    "Trims the saved media with specific given time internval and outputs as video if it is video"
    if not os.path.exists(FF_MPEG_DOWN_LOAD_MEDIA_PATH):
        return await edit_delete(
            event,
            f"a media file needs to be download, and save to the following path: `{FF_MPEG_DOWN_LOAD_MEDIA_PATH}`",
        )
    reply_to_id = await reply_id(event)
    zedevent = await edit_or_reply(event, "`Triming the media......`")
    current_message_text = event.raw_text
    cmt = current_message_text.split(" ")
    start = datetime.now()
    if len(cmt) == 3:
        # output should be video
        cmd, start_time, end_time = cmt
        o = await cult_small_video(
            FF_MPEG_DOWN_LOAD_MEDIA_PATH,
            Config.TMP_DOWNLOAD_DIRECTORY,
            start_time,
            end_time,
        )
        if o is None:
            return await edit_delete(zedevent, "**Error : **`Can't complete the process`")
        try:
            c_time = time.time()
            await event.client.send_file(
                event.chat_id,
                o,
                caption=" ".join(cmt[1:]),
                force_document=False,
                supports_streaming=True,
                allow_cache=False,
                reply_to=reply_to_id,
                progress_callback=lambda d, t: asyncio.get_running_loop().create_task(
                    progress(d, t, zedevent, c_time, "trying to upload")
                ),
            )
            os.remove(o)
        except Exception as e:
            return await edit_delete(zedevent, f"**Error : **`{e}`")
    elif len(cmt) == 2:
        # output should be image
        cmd, start_time = cmt
        o = await _zedtools.take_screen_shot(FF_MPEG_DOWN_LOAD_MEDIA_PATH, start_time)
        if o is None:
            return await edit_delete(zedevent, "**Error : **`Can't complete the process`")
        try:
            c_time = time.time()
            await event.client.send_file(
                event.chat_id,
                o,
                caption=" ".join(cmt[1:]),
                force_document=True,
                supports_streaming=True,
                allow_cache=False,
                reply_to=event.message.id,
                progress_callback=lambda d, t: asyncio.get_running_loop().create_task(
                    progress(d, t, zedevent, c_time, "trying to upload")
                ),
            )
            os.remove(o)
        except Exception as e:
            return await edit_delete(zedevent, f"**Error : **`{e}`")
    else:
        await edit_delete(zedevent, "RTFM")
        return
    end = datetime.now()
    ms = (end - start).seconds
    await edit_delete(zedevent, f"`Completed Process in {ms} seconds`", 3)


@zedub.zed_cmd(
    pattern=r"atrim(?:\s|$)([\s\S]*)",
    command=("atrim", plugin_category),
    info={
        "header": "Trims the saved media with specific given time internval and outputs as audio",
        "description": "Will trim the saved media with given time interval. and output only audio part, if no interval given it will trim whole audio",
        "usage": [
            "{tr}atrim",
            "{tr}atrim <time interval>",
        ],
        "examples": "{tr}atrim 00:00 00:10",
    },
)
async def ff_mpeg_atrim_cmd(event):
    "Trims the saved media with specific given time internval and outputs as audio"
    if not os.path.exists(FF_MPEG_DOWN_LOAD_MEDIA_PATH):
        return await edit_delete(
            event,
            f"a media file needs to be download, and save to the following path: `{FF_MPEG_DOWN_LOAD_MEDIA_PATH}`",
        )
    reply_to_id = await reply_id(event)
    zedevent = await edit_or_reply(event, "`Triming the media...........`")
    current_message_text = event.raw_text
    cmt = current_message_text.split(" ")
    start = datetime.now()
    out_put_file_name = os.path.join(Config.TMP_DOWNLOAD_DIRECTORY, f"{round(time.time())}.mp3")
    if len(cmt) == 3:
        cmd, start_time, end_time = cmt
    else:
        start_time = "00:00"
        duration = (await fileinfo(FF_MPEG_DOWN_LOAD_MEDIA_PATH))["duration"]
        end_time = readable_time(duration)
    o = await cult_small_video(
        FF_MPEG_DOWN_LOAD_MEDIA_PATH,
        Config.TMP_DOWNLOAD_DIRECTORY,
        start_time,
        end_time,
        out_put_file_name,
    )
    if o is None:
        return await edit_delete(zedevent, "**Error : **`Can't complete the process`")
    try:
        c_time = time.time()
        await event.client.send_file(
            event.chat_id,
            o,
            caption=" ".join(cmt[1:]),
            force_document=False,
            supports_streaming=True,
            allow_cache=False,
            reply_to=reply_to_id,
            progress_callback=lambda d, t: asyncio.get_running_loop().create_task(
                progress(d, t, zedevent, c_time, "trying to upload")
            ),
        )
        os.remove(o)
    except Exception as e:
        return await edit_delete(zedevent, f"**Error : **`{e}`")
    end = datetime.now()
    ms = (end - start).seconds
    await edit_delete(zedevent, f"`Completed Process in {ms} seconds`", 3)


@zedub.zed_cmd(
    pattern="ffmpegclear$",
    command=("ffmpegclear", plugin_category),
    info={
        "header": "Deletes the saved media so you can save new one",
        "description": "Only after deleting the old saved file you can add new file",
        "usage": "{tr}ffmpegclear",
    },
)
async def ff_mpeg_clear_cmd(event):
    "Deletes the saved media so you can save new one"
    if not os.path.exists(FF_MPEG_DOWN_LOAD_MEDIA_PATH):
        await edit_delete(event, "`There is no media saved in bot for triming`")
    else:
        os.remove(FF_MPEG_DOWN_LOAD_MEDIA_PATH)
        await edit_delete(
            event,
            "`The media saved in bot for triming is deleted now . you can save now new one `",
        )
