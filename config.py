import re
import sys
from os import getenv

from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()


def _safe_int(key, default=None):
    val = getenv(key)
    if val is None:
        if default is None:
            print(f"[ERROR] Required variable '{key}' is not set!", file=sys.stderr)
            sys.exit(1)
        return default
    try:
        return int(str(val).split(",")[0].strip())
    except (ValueError, TypeError):
        print(f"[ERROR] Variable '{key}' must be an integer, got: {val}", file=sys.stderr)
        sys.exit(1)


# Get this value from my.telegram.org/apps
API_ID = _safe_int("API_ID")
API_HASH = getenv("API_HASH")

# Get your token from @BotFather on Telegram.
BOT_TOKEN = getenv("BOT_TOKEN")

OWNER_USERNAME = getenv("OWNER_USERNAME", "RONALDO_MUSIC_BOT")
BOT_USERNAME = getenv("BOT_USERNAME", "RONALDO_MUSIC_ROBOT")
BOT_NAME = getenv("BOT_NAME", "RONALDO MUSIC")

# Get your mongo url from cloud.mongodb.com
MONGO_DB_URI = getenv("MONGO_DB_URI", None)

DURATION_LIMIT_MIN = _safe_int("DURATION_LIMIT", 17000)

# Chat id of a group for logging bot's activities
def _safe_logger_id(key, default=None):
    val = getenv(key)
    if val is None:
        return default
    try:
        num = int(str(val).split(",")[0].strip())
        if num > 0 and len(str(num)) >= 10:
            num = int(f"-100{num}")
        return num
    except (ValueError, TypeError):
        return default

LOGGER_ID = _safe_logger_id("LOGGER_ID", -1004476625132)

# Your Telegram user IDs (comma-separated for multiple owners)
_HARDCODED_OWNERS = [8358951104, 8148855862]
OWNER_IDS = list(_HARDCODED_OWNERS)
_owner_raw = getenv("OWNER_ID", "")
for _oid in str(_owner_raw).split(","):
    _oid_s = _oid.strip()
    if _oid_s.lstrip("-").isdigit():
        _oid_int = int(_oid_s)
        if _oid_int not in OWNER_IDS:
            OWNER_IDS.append(_oid_int)
OWNER_ID = OWNER_IDS[0]


# Bot privacy link
PRIVACY_LINK = getenv("PRIVACY_LINK", "https://t.me/Ronaldo_X_supports")

# Heroku vars (optional — only needed if deploying on Heroku)
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME", None)
HEROKU_API_KEY = getenv("HEROKU_API_KEY", None)

UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/mystricman0-cell/DARK-MUSICS",
)
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN", None)

# YouTube Data API v3 key (optional, for enhanced YouTube features)
YOUTUBE_API_KEY = getenv("YOUTUBE_API_KEY", None)

SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/Ronaldo_X_supports")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/Ronaldo_X_supports")

# Auto leave assistant after interval
AUTO_LEAVING_ASSISTANT = bool(getenv("AUTO_LEAVING_ASSISTANT", False))

# Spotify credentials from https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", None)
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", None)

# Radio / Stream URL (used as default stream when nothing else is playing)
STREAM_URL = getenv("STREAM_URL", None)

# Maximum limit for fetching playlist's tracks
PLAYLIST_FETCH_LIMIT = _safe_int("PLAYLIST_FETCH_LIMIT", 25)

# Telegram file size limits (in bytes)
TG_AUDIO_FILESIZE_LIMIT = _safe_int("TG_AUDIO_FILESIZE_LIMIT", 104857600)
TG_VIDEO_FILESIZE_LIMIT = _safe_int("TG_VIDEO_FILESIZE_LIMIT", 1073741824)

# Pyrogram v2 session strings (get from @StringFatherBot)
STRING1 = getenv("STRING_SESSION", None)
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)


BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}


START_IMG_URL = getenv(
    "START_IMG_URL", "https://files.catbox.moe/72kvx7.png"
)
START_VIDEO_URL = getenv(
    "START_VIDEO_URL", None
)
PING_IMG_URL = getenv(
    "PING_IMG_URL", "https://files.catbox.moe/72kvx7.png"
)
PLAYLIST_IMG_URL = "https://files.catbox.moe/72kvx7.png"
STATS_IMG_URL = "https://files.catbox.moe/72kvx7.png"
TELEGRAM_AUDIO_URL = "https://files.catbox.moe/72kvx7.png"
TELEGRAM_VIDEO_URL = "https://files.catbox.moe/72kvx7.png"
STREAM_IMG_URL = "https://files.catbox.moe/72kvx7.png"
SOUNCLOUD_IMG_URL = "https://files.catbox.moe/72kvx7.png"
YOUTUBE_IMG_URL = "https://files.catbox.moe/72kvx7.png"
SPOTIFY_ARTIST_IMG_URL = "https://files.catbox.moe/72kvx7.png"
SPOTIFY_ALBUM_IMG_URL = "https://files.catbox.moe/72kvx7.png"
SPOTIFY_PLAYLIST_IMG_URL = "https://files.catbox.moe/72kvx7.png"


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))


DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))


# Validate URL fields gracefully (warn only, don't crash)
def _validate_url(key, val):
    if val and not re.match("(?:http|https)://", str(val)):
        print(f"[WARNING] {key} does not start with https:// — it may not work correctly.")


_validate_url("SUPPORT_CHANNEL", SUPPORT_CHANNEL)
_validate_url("SUPPORT_CHAT", SUPPORT_CHAT)
