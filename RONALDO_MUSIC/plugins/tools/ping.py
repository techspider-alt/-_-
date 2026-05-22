from datetime import datetime

import aiohttp
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message

import config
from RONALDO_MUSIC import app
from RONALDO_MUSIC.core.call import RONALDO
from RONALDO_MUSIC.utils import bot_sys_stats
from RONALDO_MUSIC.utils.decorators.language import language
from RONALDO_MUSIC.utils.inline.extras import botplaylist_markup
from config import BANNED_USERS, PING_IMG_URL


@app.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    try:
        response = await message.reply_photo(
            photo=PING_IMG_URL,
            caption=_["ping_1"].format(app.mention),
        )
    except Exception:
        response = await message.reply_text(_["ping_1"].format(app.mention))

    start = datetime.now()
    try:
        pytgping = await RONALDO.ping()
    except Exception:
        pytgping = 0

    try:
        UP, CPU, RAM, DISK = await bot_sys_stats()
    except Exception:
        UP, CPU, RAM, DISK = "N/A", "N/A", "N/A", "N/A"

    resp = (datetime.now() - start).microseconds / 1000
    try:
        await response.edit(
            _["ping_2"].format(
                resp,
                app.mention,
                UP,
                RAM,
                CPU,
                DISK,
                pytgping,
            ),
            reply_markup=InlineKeyboardMarkup(botplaylist_markup(_)),
        )
    except Exception:
        await response.edit_text(
            f"🏓 Pong!\n\nLatency: {resp}ms\nUptime: {UP}"
        )
