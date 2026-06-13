import asyncio
import os

import httpx
import yt_dlp
from pyrogram import filters
from pyrogram.enums import ChatAction

from RONALDO_MUSIC import app
from config import BANNED_USERS, SUPPORT_CHAT


_YT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


async def _search_yt(query: str) -> dict | None:
    loop = asyncio.get_running_loop()

    def _fetch():
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "http_headers": _YT_HEADERS,
            "extractor_args": {
                "youtube": {"player_client": ["tv_embedded", "ios"]}
            },
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if not info or not info.get("entries"):
            return None
        entry = info["entries"][0]
        vid_id = entry.get("id", "")
        dur_sec = entry.get("duration") or 0
        dur_str = f"{int(dur_sec // 60)}:{int(dur_sec % 60):02d}"
        thumb = entry.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        return {
            "title": (entry.get("title") or "Unknown")[:50],
            "url": f"https://www.youtube.com/watch?v={vid_id}",
            "vid_id": vid_id,
            "duration": dur_str,
            "duration_sec": int(dur_sec),
            "thumb": thumb,
            "views": str(entry.get("view_count") or "?"),
        }

    try:
        return await asyncio.wait_for(loop.run_in_executor(None, _fetch), timeout=20)
    except Exception:
        return None


async def _download_audio(url: str) -> str | None:
    loop = asyncio.get_running_loop()
    os.makedirs("downloads", exist_ok=True)

    def _fetch():
        for player_client in [["tv_embedded"], ["ios"], ["android_embedded"], ["web"]]:
            try:
                ydl_opts = {
                    "format": "bestaudio[ext=m4a]/bestaudio/best",
                    "outtmpl": "downloads/%(id)s.%(ext)s",
                    "geo_bypass": True,
                    "nocheckcertificate": True,
                    "quiet": True,
                    "no_warnings": True,
                    "nopart": True,
                    "retries": 3,
                    "socket_timeout": 30,
                    "http_headers": _YT_HEADERS,
                    "extractor_args": {"youtube": {"player_client": player_client}},
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "128",
                    }],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    vid_id = info.get("id", "unknown")
                mp3 = f"downloads/{vid_id}.mp3"
                if os.path.exists(mp3):
                    return mp3
                for ext in ["m4a", "webm", "opus", "ogg"]:
                    path = f"downloads/{vid_id}.{ext}"
                    if os.path.exists(path):
                        return path
            except Exception:
                continue
        return None

    try:
        return await asyncio.wait_for(loop.run_in_executor(None, _fetch), timeout=120)
    except Exception:
        return None


@app.on_message(filters.command(["song", "music"]) & ~BANNED_USERS)
async def song_cmd(client, message):
    try:
        await message.delete()
    except Exception:
        pass

    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_mention = f"[{user_name}](tg://user?id={user_id})"

    if len(message.command) < 2:
        return await message.reply("**» sᴏɴɢ ɴᴀᴍᴇ ᴅᴏ ʙᴀʙʏ!**\n\n**ᴜsᴀɢᴇ:** `/song song name`")

    query = message.text.split(None, 1)[1].strip()
    m = await message.reply("**» 🔍 sᴇᴀʀᴄʜɪɴɢ, ᴩʟᴇᴀsᴇ ᴡᴀɪᴛ...**")

    result = await _search_yt(query)
    if not result:
        return await m.edit("**😴 sᴏɴɢ ɴᴏᴛ ꜰᴏᴜɴᴅ ᴏɴ ʏᴏᴜᴛᴜʙᴇ.**\n\n» ᴍᴀʏʙᴇ ᴛᴜɴᴇ ɢᴀʟᴀᴛ ʟɪᴋʜᴀ ʜᴏ!")

    await m.edit("**» ⬇️ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ...**\n\nᴩʟᴇᴀsᴇ ᴡᴀɪᴛ...")
    try:
        await app.send_chat_action(message.chat.id, ChatAction.UPLOAD_AUDIO)
    except Exception:
        pass

    audio_file = await _download_audio(result["url"])
    if not audio_file:
        return await m.edit(
            f"**❌ ᴅᴏᴡɴʟᴏᴀᴅ ꜰᴀɪʟᴇᴅ!**\n\n"
            f"YouTube blocked download. Try again later.\n"
            f"[Support]({SUPPORT_CHAT})"
        )

    thumb_path = None
    try:
        async with httpx.AsyncClient(timeout=10) as hx:
            resp = await hx.get(result["thumb"])
            if resp.status_code == 200:
                thumb_path = f"downloads/thumb_{result['vid_id']}.jpg"
                with open(thumb_path, "wb") as f:
                    f.write(resp.content)
    except Exception:
        pass

    caption = (
        f"**ᴛɪᴛʟᴇ :** {result['title']}\n"
        f"**ᴅᴜʀᴀᴛɪᴏɴ :** `{result['duration']}`\n"
        f"**ᴠɪᴇᴡs :** `{result['views']}`\n"
        f"**ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ »** {user_mention}"
    )

    try:
        await message.reply_audio(
            audio=audio_file,
            caption=caption,
            performer=app.name,
            thumb=thumb_path,
            title=result["title"],
            duration=result["duration_sec"],
        )
        await m.delete()
    except Exception as e:
        await m.edit(f"**❌ ᴅᴏᴡɴʟᴏᴀᴅ ᴇʀʀᴏʀ:** `{e}`")
    finally:
        for f in [audio_file, thumb_path]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
