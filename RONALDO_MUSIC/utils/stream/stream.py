import asyncio
import os
import logging
from random import randint
from typing import Union

from pyrogram.types import InlineKeyboardMarkup

import config
from RONALDO_MUSIC import Carbon, YouTube, app
from RONALDO_MUSIC.core.call import RONALDO
from RONALDO_MUSIC.misc import db


from RONALDO_MUSIC.utils.database import add_active_video_chat, is_active_chat
from RONALDO_MUSIC.utils.exceptions import AssistantErr
from RONALDO_MUSIC.utils.inline import (
    aq_markup,
    close_markup,
    stream_markup,
    telegram_markup,
)
from RONALDO_MUSIC.utils.pastebin import RONALDOBin
from RONALDO_MUSIC.utils.logger_card import send_logger_card
from RONALDO_MUSIC.utils.stream.queue import put_queue, put_queue_index
from RONALDO_MUSIC.utils.thumbnails import get_thumb


async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):
    if not result:
        return
    if forceplay:
        await RONALDO.force_stop_stream(chat_id)
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                (
                    title,
                    duration_min,
                    duration_sec,
                    thumbnail,
                    vidid,
                ) = await YouTube.details(search, False if spotify else True)
            except:
                continue
            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue
            if await is_active_chat(chat_id) and db.get(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n"
                msg += f"{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                status = True if video else None
                try:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, video=status, videoid=True
                    )
                except Exception:
                    try:
                        file_path, direct = await YouTube.download(
                            vidid, mystic, video=status, videoid=True
                        )
                    except Exception:
                        raise AssistantErr(_["play_14"])
                await RONALDO.join_call(
                    chat_id,
                    original_chat_id,
                    file_path,
                    video=status,
                    image=thumbnail,
                )
                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path if direct else f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                    forceplay=forceplay,
                )
                img = await get_thumb(vidid)
                button = stream_markup(_, vidid, chat_id)
                run = await app.send_photo(
                    original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{vidid}",
                        title[:23],
                        duration_min,
                        user_name,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
        if count == 0:
            return
        else:
            link = await RONALDOBin(msg)
            lines = msg.count("\n")
            if lines >= 17:
                car = os.linesep.join(msg.split(os.linesep)[:17])
            else:
                car = msg
            carbon = await Carbon.generate(car, randint(100, 10000000))
            upl = close_markup(_)
            return await app.send_photo(
                original_chat_id,
                photo=carbon,
                caption=_["play_21"].format(position, link),
                reply_markup=upl,
            )
    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]
        status = True if video else None
        last_dl_err = None
        downloaded = False

        # Attempt 1 & 2: normal download with retries (no sleep — fail fast)
        for _attempt in range(2):
            try:
                file_path, direct = await YouTube.download(
                    vidid, mystic, videoid=True, video=status
                )
                downloaded = True
                break
            except Exception as _e:
                last_dl_err = _e

        # Attempt 3: bot blocked — try Spotify-assisted alternative search
        if not downloaded:
            try:
                from RONALDO_MUSIC.platforms.Youtube import _is_bot_blocked, _ydl_search
                from RONALDO_MUSIC.platforms.Youtube import _spotify_search_track
                _bot_err = _is_bot_blocked(last_dl_err)
                alt_vidid = None

                if _bot_err:
                    # Try Spotify to find the real title, then search YT again
                    sp_info = await _spotify_search_track(title)
                    if sp_info and sp_info.get("search_query"):
                        alt_info = await _ydl_search(sp_info["search_query"], is_url=False)
                        if alt_info:
                            alt_vidid = alt_info["vidid"]
                    # If Spotify didn't help, just search by title directly
                    if not alt_vidid:
                        alt_info = await _ydl_search(f"{title} audio", is_url=False)
                        if alt_info:
                            alt_vidid = alt_info["vidid"]

                if alt_vidid and alt_vidid != vidid:
                    try:
                        file_path, direct = await YouTube.download(
                            alt_vidid, mystic, videoid=True, video=status
                        )
                        vidid = alt_vidid
                        downloaded = True
                    except Exception:
                        pass
            except Exception:
                pass

        if not downloaded:
            # Show a clean user-friendly error instead of raw yt-dlp error
            from RONALDO_MUSIC.platforms.Youtube import _is_bot_blocked
            if _is_bot_blocked(last_dl_err):
                raise AssistantErr(
                    "⚠️ <b>YouTube ɴᴇ ʙʟᴏᴄᴋ ᴋɪʏᴀ!</b>\n\n"
                    "YouTube ᴀʙʜɪ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴀʜɪ ᴅᴇ ʀᴀʜᴀ.\n"
                    "ᴋᴜᴄʜ ᴅᴇʀ ʙᴀᴀᴅ ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋᴀʀᴏ ʏᴀ ᴋᴏɪ ᴅᴜsʀᴀ ɢᴀᴀɴᴀ ᴄʜᴜɴᴏ.\n\n"
                    "💡 ᴛɪᴘ: Sᴘᴏᴛɪꜰʏ ʏᴀ SᴏᴜɴᴅCʟᴏᴜᴅ ʟɪɴᴋ ᴛʀʏ ᴋᴀʀᴏ!"
                )
            raise AssistantErr(
                "❍ <b>ᴅᴏᴡɴʟᴏᴀᴅ ꜰᴀɪʟᴇᴅ!</b>\n\n"
                "ɢᴀᴀɴᴀ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴀʜɪ ʜᴜᴀ. ᴋᴏɪ ᴅᴜsʀᴀ ɢᴀᴀɴᴀ ᴛʀʏ ᴋᴀʀᴏ."
            )
        if await is_active_chat(chat_id) and db.get(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await RONALDO.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
                image=thumbnail,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await get_thumb(vidid)
            button = stream_markup(_, vidid, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:23],
                    duration_min,
                    user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=True,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            await send_logger_card(chat_id, original_chat_id, title, user_name, "VIDEO" if video else "AUDIO")
    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result["title"]
        duration_min = result["duration_min"]
        if await is_active_chat(chat_id) and db.get(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await RONALDO.join_call(chat_id, original_chat_id, file_path, video=None)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
                forceplay=forceplay,
            )
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=_["stream_1"].format(
                    config.SUPPORT_CHAT, title[:23], duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=True,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await send_logger_card(chat_id, original_chat_id, title, user_name, "AUDIO")
    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = (result["title"]).title()
        duration_min = result["dur"]
        status = True if video else None
        if await is_active_chat(chat_id) and db.get(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await RONALDO.join_call(chat_id, original_chat_id, file_path, video=status)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            if video:
                await add_active_video_chat(chat_id)
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.TELEGRAM_VIDEO_URL if video else config.TELEGRAM_AUDIO_URL,
                caption=_["stream_1"].format(link, title[:23], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=True,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await send_logger_card(chat_id, original_chat_id, title, user_name, "VIDEO" if video else "AUDIO")
    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        thumbnail = result["thumb"]
        duration_min = "Live Track"
        status = True if video else None
        if await is_active_chat(chat_id) and db.get(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])
            await RONALDO.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
                image=thumbnail if thumbnail else None,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await get_thumb(vidid)
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:23],
                    duration_min,
                    user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=True,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await send_logger_card(chat_id, original_chat_id, title, user_name, "VIDEO" if video else "AUDIO")
    elif streamtype == "index":
        link = result
        title = "ɪɴᴅᴇx ᴏʀ ᴍ3ᴜ8 ʟɪɴᴋ"
        duration_min = "00:00"
        if await is_active_chat(chat_id) and db.get(chat_id):
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await mystic.edit_text(
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await RONALDO.join_call(
                chat_id,
                original_chat_id,
                link,
                video=True if video else None,
            )
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=_["stream_2"].format(user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await mystic.delete()
