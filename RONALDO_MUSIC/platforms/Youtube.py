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

# Spotify search fallback — used when YouTube throttles
async def _spotify_search_track(query: str) -> dict | None:
    """Search Spotify for a track and return YT-compatible dict using title+artist."""
    try:
        import config
        if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
            return None
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        loop = asyncio.get_running_loop()

        def _fetch():
            sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
            ))
            results = sp.search(q=query, limit=1, type="track")
            items = results.get("tracks", {}).get("items", [])
            if not items:
                return None
            track = items[0]
            name = track["name"]
            artists = " ".join(a["name"] for a in track["artists"])
            duration_ms = track["duration_ms"]
            duration_sec = duration_ms // 1000
            duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}"
            thumb = ""
            images = track.get("album", {}).get("images", [])
            if images:
                thumb = images[0]["url"]
            return {
                "title": f"{name} {artists}",
                "search_query": f"{name} {artists}",
                "duration_min": duration_min,
                "thumb": thumb,
                "vidid": None,
                "link": None,
                "_spotify": True,
            }

        return await asyncio.wait_for(loop.run_in_executor(None, _fetch), timeout=10)
    except Exception:
        return None


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


def _is_bot_blocked(err: Exception) -> bool:
    """Check if error means video is actually unavailable (not just bot-detection)."""
    msg = str(err).lower()
    # Only stop retrying for truly unavailable/private content — NOT for bot-detection errors
    return any(x in msg for x in [
        "private video", "video unavailable", "this video is not available",
        "has been removed", "account associated",
    ])


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
            "nocheckcertificate": True,
            "geo_bypass": True,
            "http_headers": _YT_HEADERS,
            "extractor_args": {
                "youtube": {
                    "player_client": ["tv_embedded", "android_embedded"],
                }
            },
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


def _get_yt_title(link: str) -> str | None:
    """
    Try to extract just the video title from YouTube without downloading.
    Used as a query for the SoundCloud fallback.
    """
    try:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "logtostderr": False,
            "socket_timeout": 10,
            "extractor_args": {
                "youtube": {
                    "player_client": ["tv_embedded"],
                    "player_skip": ["webpage", "configs"],
                }
            },
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=False)
            return info.get("title") if info else None
    except Exception:
        pass
    # Try oembed as last resort (no API key needed, returns title for public videos)
    try:
        import urllib.request as _ur, urllib.parse as _up, json as _json
        oembed_url = f"https://www.youtube.com/oembed?url={_up.quote(link)}&format=json"
        req = _ur.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with _ur.urlopen(req, timeout=8) as r:
            data = _json.loads(r.read())
            return data.get("title")
    except Exception:
        return None


def _soundcloud_fallback_dl(query: str, vid_id: str = "sc_fallback") -> str:
    """
    Fallback: search SoundCloud for the given query and download best audio.
    SoundCloud works from server/datacenter IPs without cookies.
    Called when YouTube download fails due to IP-based bot detection.
    Tries progressively shorter queries to maximise hit rate.
    """
    os.makedirs("downloads", exist_ok=True)

    # Build candidate queries: full → first 5 words → first 3 words
    words = query.split()
    queries = [query]
    if len(words) > 5:
        queries.append(" ".join(words[:5]))
    if len(words) > 3:
        queries.append(" ".join(words[:3]))

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"downloads/sc_{vid_id}.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "logtostderr": False,
        "nocheckcertificate": True,
        "socket_timeout": 30,
        "retries": 3,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    for q in queries:
        sc_query = f"scsearch1:{q}"
        try:
            # First check if query has results (extract_flat is fast)
            check_opts = {"quiet": True, "no_warnings": True, "logtostderr": False,
                          "extract_flat": True, "socket_timeout": 10}
            with yt_dlp.YoutubeDL(check_opts) as ydl:
                check = ydl.extract_info(sc_query, download=False)
            entries = list(check.get("entries", [])) if check else []
            if not entries:
                continue  # try shorter query

            # Found results — download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(sc_query, download=True)
                if info and "entries" in info:
                    entries_dl = list(info["entries"])
                    info = entries_dl[0] if entries_dl else None
                if not info:
                    continue
                sc_id = info.get("id", vid_id)

            # Locate downloaded file
            for name in [f"sc_{vid_id}", f"sc_{sc_id}"]:
                mp3_path = os.path.join("downloads", f"{name}.mp3")
                if os.path.exists(mp3_path):
                    return mp3_path
                for ext in ["m4a", "webm", "opus", "ogg"]:
                    candidate = os.path.join("downloads", f"{name}.{ext}")
                    if os.path.exists(candidate):
                        return candidate
        except Exception:
            continue

    raise Exception(f"SoundCloud: no results for '{query}' — YouTube cookies needed")


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

        # Spotify fallback — search by title via Spotify, then re-fetch from YT
        sp_info = await _spotify_search_track(link)
        if sp_info:
            yt_retry = await _ydl_search(sp_info["search_query"], is_url=False)
            if yt_retry:
                dur_min = yt_retry["duration_min"] or "0:00"
                dur_sec = int(time_to_seconds(dur_min)) if yt_retry["duration_min"] else 0
                return yt_retry["title"], dur_min, dur_sec, yt_retry["thumb"], yt_retry["vidid"]
            dur_min = sp_info.get("duration_min", "0:00")
            dur_sec = int(time_to_seconds(dur_min)) if dur_min else 0
            fake_vidid = "spotify_" + re.sub(r"\W+", "_", sp_info["title"])[:20]
            return sp_info["title"], dur_min, dur_sec, sp_info.get("thumb", ""), fake_vidid

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

        # yt-dlp fallback
        is_url = bool(_YT_REGEX.search(link))
        info = await _ydl_search(link, is_url=is_url)
        if info:
            return info, info["vidid"]

        # Spotify search fallback — when YT throttles/blocks
        sp_info = await _spotify_search_track(link)
        if sp_info:
            # Use Spotify title to search YT one more time
            yt_retry = await _ydl_search(sp_info["search_query"], is_url=False)
            if yt_retry:
                return yt_retry, yt_retry["vidid"]
            # Return Spotify metadata with a dummy vidid for display
            sp_info["vidid"] = "spotify_" + re.sub(r"\W+", "_", sp_info["title"])[:20]
            sp_info["link"] = f"https://www.youtube.com/results?search_query={sp_info['search_query'].replace(' ', '+')}"
            return sp_info, sp_info["vidid"]

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
            last_err = None
            has_cookies = bool(cookies)

            # ── Build attempt list ──────────────────────────────────────────────
            # With cookies: use web client (most reliable with cookies)
            # Without cookies: try all embedded/mobile clients that don't need login
            if has_cookies:
                client_attempts = [
                    (["web"],         {}),
                    (["tv_embedded"], {"player_skip": ["webpage", "configs"]}),
                    (["ios"],         {"player_skip": ["webpage", "configs"]}),
                    (["android_embedded"], {"player_skip": ["webpage", "configs"]}),
                    (["mweb"],        {"player_skip": ["webpage"]}),
                ]
            else:
                # android comes first — uses YouTube's mobile API endpoint which
                # is the most reliable on server/VPS IPs without cookies (2025).
                # tv_embedded is often blocked; ios/mweb as fallbacks.
                client_attempts = [
                    (["android"],          {"player_skip": ["webpage", "configs"]}),
                    (["ios"],              {"player_skip": ["webpage", "configs"]}),
                    (["tv_embedded"],      {"player_skip": ["webpage", "configs"]}),
                    (["android_embedded"], {"player_skip": ["webpage", "configs"]}),
                    (["mweb"],             {"player_skip": ["webpage"]}),
                    (["web_creator"],      {}),
                ]

            for player_client, extra_args in client_attempts:
                try:
                    ydl_optssx = {
                        # 140 = guaranteed m4a 128kbps on virtually all YT videos,
                        # no auth required. Falls back to bestaudio for non-YT sources.
                        "format": "140/bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
                        "outtmpl": "downloads/%(id)s.%(ext)s",
                        "geo_bypass": True,
                        "nocheckcertificate": True,
                        "quiet": True,
                        "no_warnings": True,
                        "logtostderr": False,
                        "nopart": True,
                        # Reduced retries & timeout — fail fast, try next client
                        "retries": 1,
                        "fragment_retries": 1,
                        "socket_timeout": 12,
                        "http_headers": _YT_HEADERS,
                        "prefer_free_formats": True,
                        "extractor_args": {
                            "youtube": {
                                "player_client": player_client,
                                **extra_args,
                            }
                        },
                        # No FFmpegExtractAudio postprocessor — pytgcalls uses FFmpeg
                        # internally so m4a/webm/opus plays directly, saves 10-30s per song
                        **cookies,
                    }
                    x = yt_dlp.YoutubeDL(ydl_optssx)
                    info = x.extract_info(link, download=True)
                    vid_id = info.get("id", "unknown")
                    for ext in ["m4a", "webm", "opus", "ogg", "mp3"]:
                        candidate = os.path.join("downloads", f"{vid_id}.{ext}")
                        if os.path.exists(candidate):
                            return candidate
                    return os.path.join("downloads", f"{vid_id}.{info.get('ext', 'webm')}")
                except Exception as e:
                    last_err = e
                    if _is_bot_blocked(e):
                        break
                    continue

            # Last resort: SoundCloud fallback
            # Piped/Invidious instances are unreliable from server IPs.
            # SoundCloud works without cookies — extract YT title, search SC.
            try:
                # Get video ID for filename
                import re as _re2
                _vid_match = _re2.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", link)
                _vid_id = _vid_match.group(1) if _vid_match else "yt_sc"
                # Try to get title from YouTube oembed (lightweight, usually works)
                _title = _get_yt_title(link) or _vid_id
                return _soundcloud_fallback_dl(_title, _vid_id)
            except Exception as ep:
                last_err = ep
            raise Exception(f"Download failed: {last_err}")

        def video_dl():
            os.makedirs("downloads", exist_ok=True)
            last_err = None
            has_cookies = bool(cookies)

            if has_cookies:
                client_attempts = [
                    (["web"],         {}),
                    (["tv_embedded"], {"player_skip": ["webpage", "configs"]}),
                    (["ios"],         {"player_skip": ["webpage", "configs"]}),
                    (["android_embedded"], {"player_skip": ["webpage", "configs"]}),
                ]
            else:
                # android first — best for server/VPS IPs without cookies
                client_attempts = [
                    (["android"],          {"player_skip": ["webpage", "configs"]}),
                    (["ios"],              {"player_skip": ["webpage", "configs"]}),
                    (["tv_embedded"],      {"player_skip": ["webpage", "configs"]}),
                    (["android_embedded"], {"player_skip": ["webpage", "configs"]}),
                    (["mweb"],             {"player_skip": ["webpage"]}),
                    (["web_creator"],      {}),
                ]

            for player_client, extra_args in client_attempts:
                try:
                    ydl_optssx = {
                        "format": "(bestvideo[height<=?720][ext=mp4])+(bestaudio)/bestvideo[height<=?720]+bestaudio/best",
                        "outtmpl": "downloads/%(id)s.%(ext)s",
                        "geo_bypass": True,
                        "nocheckcertificate": True,
                        "quiet": True,
                        "no_warnings": True,
                        "logtostderr": False,
                        "merge_output_format": "mp4",
                        "retries": 3,
                        "fragment_retries": 3,
                        "socket_timeout": 30,
                        "http_headers": _YT_HEADERS,
                        "extractor_args": {
                            "youtube": {
                                "player_client": player_client,
                                **extra_args,
                            }
                        },
                        **cookies,
                    }
                    x = yt_dlp.YoutubeDL(ydl_optssx)
                    info = x.extract_info(link, download=True)
                    vid_id = info.get("id", "unknown")
                    candidate = os.path.join("downloads", f"{vid_id}.mp4")
                    if os.path.exists(candidate):
                        return candidate
                    return os.path.join("downloads", f"{vid_id}.{info.get('ext', 'mp4')}")
                except Exception as e:
                    last_err = e
                    if _is_bot_blocked(e):
                        break
                    continue
            raise Exception(f"Video download failed: {last_err}")

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
