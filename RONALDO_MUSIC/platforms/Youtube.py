import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from RONALDO_MUSIC.utils.database import is_on_off
from RONALDO_MUSIC.utils.formatters import time_to_seconds


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


cookies_file = "RONALDO_MUSIC/assets/cookies.txt"

_YT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_YT_REGEX = re.compile(r"(?:youtube\.com|youtu\.be)")


def _cookies_opts() -> dict:
    """Return cookiefile option only when file has real cookie data (> 300 bytes)."""
    try:
        if os.path.exists(cookies_file) and os.path.getsize(cookies_file) > 300:
            return {"cookiefile": cookies_file}
    except Exception:
        pass
    return {}


async def _ydl_search(query: str, is_url: bool = False) -> dict | None:
    """
    yt-dlp based YouTube search — used as primary/fallback.
    Runs in executor so it never blocks the event loop.
    """
    loop = asyncio.get_running_loop()

    def _fetch():
        search_q = query if is_url else f"ytsearch1:{query}"
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "http_headers": _YT_HEADERS,
            **_cookies_opts(),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_q, download=False)
        if not info:
            return None
        entry = info
        if info.get("entries"):
            entry = info["entries"][0]
        if not entry:
            return None
        vid_id = entry.get("id", "")
        if not vid_id:
            return None
        dur_sec = entry.get("duration") or 0
        dur_min = f"{int(dur_sec // 60)}:{int(dur_sec % 60):02d}" if dur_sec else None
        title = entry.get("title") or "Unknown Title"
        thumb = (
            entry.get("thumbnail")
            or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        )
        return {
            "title": title,
            "link": f"https://www.youtube.com/watch?v={vid_id}",
            "vidid": vid_id,
            "duration_min": dur_min,
            "thumb": thumb,
        }

    try:
        return await asyncio.wait_for(loop.run_in_executor(None, _fetch), timeout=30)
    except Exception:
        return None


async def _vsearch_next(link: str, limit: int = 1) -> list:
    """Run VideosSearch with timeout. Returns result list or empty list."""
    try:
        results = VideosSearch(link, limit=limit)
        data = await asyncio.wait_for(results.next(), timeout=8)
        return data.get("result", []) or []
    except Exception:
        return []


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset is None:
            return None
        return text[offset: offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        result_list = await _vsearch_next(link, limit=1)
        if result_list:
            result = result_list[0]
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = 0 if str(duration_min) == "None" else int(time_to_seconds(duration_min))
            return title, duration_min, duration_sec, thumbnail, vidid

        # yt-dlp fallback
        is_url = bool(_YT_REGEX.search(link))
        info = await _ydl_search(link, is_url=is_url)
        if info:
            dur_min = info["duration_min"] or "0:00"
            dur_sec = int(time_to_seconds(dur_min)) if info["duration_min"] else 0
            return info["title"], dur_min, dur_sec, info["thumb"], info["vidid"]

        raise Exception("Failed to fetch track details from YouTube")

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        result_list = await _vsearch_next(link)
        if result_list:
            return result_list[0]["title"]
        info = await _ydl_search(link, is_url=bool(_YT_REGEX.search(link)))
        return info["title"] if info else "Unknown"

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        result_list = await _vsearch_next(link)
        if result_list:
            return result_list[0]["duration"]
        info = await _ydl_search(link, is_url=bool(_YT_REGEX.search(link)))
        return info["duration_min"] if info else "0:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        result_list = await _vsearch_next(link)
        if result_list:
            return result_list[0]["thumbnails"][0]["url"].split("?")[0]
        info = await _ydl_search(link, is_url=bool(_YT_REGEX.search(link)))
        return info["thumb"] if info else ""

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        cookies = _cookies_opts()
        cmd = ["yt-dlp", "-g", "-f", "best[height<=?720][width<=?1280]"]
        if cookies:
            cmd += ["--cookies", cookies_file]
        cmd += ["--add-header", f"User-Agent:{_YT_HEADERS['User-Agent']}"]
        cmd.append(link)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        cookies = _cookies_opts()
        cookie_arg = f"--cookies {cookies_file}" if cookies else ""
        playlist = await shell_cmd(
            f"yt-dlp {cookie_arg} -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = [k for k in playlist.split("\n") if k]
        except Exception:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        # Try YoutubeSearchPython first (fast when it works)
        result_list = await _vsearch_next(link, limit=1)
        if result_list:
            result = result_list[0]
            track_details = {
                "title": result["title"],
                "link": result["link"],
                "vidid": result["id"],
                "duration_min": result["duration"],
                "thumb": result["thumbnails"][0]["url"].split("?")[0],
            }
            return track_details, result["id"]

        # yt-dlp fallback — always works
        is_url = bool(_YT_REGEX.search(link))
        info = await _ydl_search(link, is_url=is_url)
        if info:
            return info, info["vidid"]

        raise Exception("Could not find track. Try a different query.")

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {
            "quiet": True,
            "http_headers": _YT_HEADERS,
            **_cookies_opts(),
        }
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for fmt in r.get("formats", []):
                try:
                    str(fmt["format"])
                except Exception:
                    continue
                if "dash" in str(fmt["format"]).lower():
                    continue
                try:
                    formats_available.append({
                        "format": fmt["format"],
                        "filesize": fmt["filesize"],
                        "format_id": fmt["format_id"],
                        "ext": fmt["ext"],
                        "format_note": fmt["format_note"],
                        "yturl": link,
                    })
                except Exception:
                    continue
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        result_list = await _vsearch_next(link, limit=10)
        if result_list and query_type < len(result_list):
            result = result_list[query_type]
            return (
                result["title"],
                result["duration"],
                result["thumbnails"][0]["url"].split("?")[0],
                result["id"],
            )

        # yt-dlp fallback — return first result regardless of query_type
        info = await _ydl_search(link, is_url=bool(_YT_REGEX.search(link)))
        if info:
            return info["title"], info["duration_min"] or "0:00", info["thumb"], info["vidid"]
        raise Exception("Slider query failed")

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()
        cookies = _cookies_opts()

        def audio_dl():
            os.makedirs("downloads", exist_ok=True)
            ydl_optssx = {
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "nopart": True,
                "retries": 5,
                "socket_timeout": 30,
                "http_headers": _YT_HEADERS,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                **cookies,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            vid_id = info.get("id", "unknown")
            mp3_path = os.path.join("downloads", f"{vid_id}.mp3")
            if os.path.exists(mp3_path):
                return mp3_path
            x.download([link])
            if os.path.exists(mp3_path):
                return mp3_path
            for ext in ["mp3", "m4a", "webm", "opus", "ogg"]:
                candidate = os.path.join("downloads", f"{vid_id}.{ext}")
                if os.path.exists(candidate):
                    return candidate
            return os.path.join("downloads", f"{vid_id}.{info.get('ext', 'webm')}")

        def video_dl():
            os.makedirs("downloads", exist_ok=True)
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])/bestvideo[height<=?720]+bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "merge_output_format": "mp4",
                "retries": 5,
                "socket_timeout": 30,
                "http_headers": _YT_HEADERS,
                **cookies,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            vid_id = info.get("id", "unknown")
            candidate = os.path.join("downloads", f"{vid_id}.mp4")
            if os.path.exists(candidate):
                return candidate
            x.download([link])
            if os.path.exists(candidate):
                return candidate
            return os.path.join("downloads", f"{vid_id}.{info.get('ext', 'mp4')}")

        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
                "http_headers": _YT_HEADERS,
                **cookies,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "http_headers": _YT_HEADERS,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                **cookies,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            return f"downloads/{title}.mp4"
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            return f"downloads/{title}.mp3"
        elif video:
            if await is_on_off(1):
                direct = True
                downloaded_file = await loop.run_in_executor(None, video_dl)
            else:
                cookies_arg = ["--cookies", cookies_file] if cookies else []
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    *cookies_arg,
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
                    f"{link}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if stdout:
                    downloaded_file = stdout.decode().split("\n")[0]
                    direct = None
                else:
                    return
        else:
            direct = True
            downloaded_file = await loop.run_in_executor(None, audio_dl)
        return downloaded_file, direct
