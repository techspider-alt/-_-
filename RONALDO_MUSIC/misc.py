import socket
import time

from pyrogram import filters

import config
from RONALDO_MUSIC.core.mongo import mongodb

from .logging import LOGGER

SUDOERS = filters.user()
HAPP = None
_boot_ = time.time()

try:
    import heroku3 as _heroku3_mod
    _heroku3_available = True
except ImportError:
    _heroku3_mod = None
    _heroku3_available = False


def is_heroku():
    try:
        return "heroku" in socket.getfqdn()
    except Exception:
        return False


XCB = [
    "/",
    "@",
    ".",
    "com",
    ":",
    "git",
    "heroku",
    "push",
    str(config.HEROKU_API_KEY) if config.HEROKU_API_KEY else "",
    "https",
    str(config.HEROKU_APP_NAME) if config.HEROKU_APP_NAME else "",
    "HEAD",
    "master",
]


def dbb():
    global db
    db = {}
    LOGGER(__name__).info(f"𝗗𝗔𝗧𝗔𝗕𝗔𝗦𝗘 𝗟𝗢𝗔𝗗 𝗕𝗔𝗕𝗬🍫........")


async def sudo():
    for owner_id in config.OWNER_IDS:
        SUDOERS.add(owner_id)
    sudoersdb = mongodb.sudoers
    sudoers_doc = await sudoersdb.find_one({"sudo": "sudo"})
    sudoers = [] if not sudoers_doc else sudoers_doc.get("sudoers", [])
    changed = False
    for owner_id in config.OWNER_IDS:
        if owner_id not in sudoers:
            sudoers.append(owner_id)
            changed = True
    if changed:
        await sudoersdb.update_one(
            {"sudo": "sudo"},
            {"$set": {"sudoers": sudoers}},
            upsert=True,
        )
    for user_id in sudoers:
        SUDOERS.add(user_id)
    LOGGER(__name__).info(f"𝗦𝗨𝗗𝗢 𝗨𝗦𝗘𝗥 𝗗𝗢𝗡𝗘✨🎋.")


def heroku():
    global HAPP
    if not _heroku3_available:
        return
    try:
        if is_heroku() and config.HEROKU_API_KEY and config.HEROKU_APP_NAME:
            Heroku = _heroku3_mod.from_key(config.HEROKU_API_KEY)
            HAPP = Heroku.app(config.HEROKU_APP_NAME)
            LOGGER(__name__).info(f"🍟𝗛𝗘𝗥𝗢𝗞𝗨 𝗔𝗣𝗣 𝗡𝗔𝗠𝗘 𝗟𝗢𝗔𝗗......💦..")
    except Exception as e:
        LOGGER(__name__).warning(f"Heroku setup skipped: {e}")
