import asyncio

import aiohttp
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from RONALDO_MUSIC import app
from config import BANNED_USERS, lyrical
import random
import string


@app.on_message(
    filters.command(["lyrics", "lyric", "lyri"], prefixes=["/", "!", "."])
    & ~BANNED_USERS
)
async def lyrics_command(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❍ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ sᴏɴɢ ɴᴀᴍᴇ.\n\n<b>ᴇxᴀᴍᴘʟᴇ:</b> <code>/lyrics Shape of You</code>"
        )

    query = message.text.split(None, 1)[1].strip()
    m = await message.reply_text(f"❍ ꜱᴇᴀʀᴄʜɪɴɢ ʟʏʀɪᴄs ꜰᴏʀ: <b>{query}</b>...")

    lyrics = None

    # Try lyrics.ovh first (free, no API key needed)
    try:
        parts = query.rsplit(" ", 1)
        if len(parts) == 2:
            artist, title = parts[0], parts[1]
        else:
            artist, title = query, query

        url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lyrics = data.get("lyrics", "")
    except Exception:
        pass

    # Fallback: try with full query as both artist and title
    if not lyrics:
        try:
            encoded = query.replace(" ", "%20")
            url = f"https://api.lyrics.ovh/v1/{encoded}/{encoded}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        lyrics = data.get("lyrics", "")
        except Exception:
            pass

    if not lyrics:
        return await m.edit(
            f"❍ ʟʏʀɪᴄs ɴᴏᴛ ꜰᴏᴜɴᴅ ꜰᴏʀ: <b>{query}</b>\n\n"
            "ᴛʀʏ ᴡɪᴛʜ ꜰᴜʟʟ ꜱᴏɴɢ ɴᴀᴍᴇ ᴏʀ ᴀʀᴛɪꜱᴛ ɴᴀᴍᴇ."
        )

    ran_hash = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    lyrical[ran_hash] = lyrics

    upl = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                text="📖 ᴠɪᴇᴡ ʟʏʀɪᴄs",
                url=f"https://t.me/{app.username}?start=lyrics_{ran_hash}",
            )
        ]]
    )

    preview = lyrics[:200] + "..." if len(lyrics) > 200 else lyrics
    await m.edit(
        f"🎵 <b>ʟʏʀɪᴄs ꜰᴏᴜɴᴅ!</b>\n\n"
        f"<i>{preview}</i>\n\n"
        f"ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ʀᴇᴀᴅ ꜰᴜʟʟ ʟʏʀɪᴄs 👇",
        reply_markup=upl,
    )
