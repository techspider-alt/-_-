from pyrogram import filters
from pyrogram.types import Message

from RONALDO_MUSIC import app
from RONALDO_MUSIC.misc import SUDOERS
from RONALDO_MUSIC.utils.database import (
    autoplay_on,
    autoplay_off,
    is_autoplay,
    get_lang,
    is_active_chat,
)
from config import BANNED_USERS
from strings import get_string


@app.on_message(
    filters.command(["autoplay", "ap"], prefixes=["/", "!", "."])
    & filters.group
    & ~BANNED_USERS
)
async def autoplay_command(client, message: Message):
    chat_id = message.chat.id
    language = await get_lang(chat_id)
    _ = get_string(language)

    # Toggle
    current = await is_autoplay(chat_id)

    if current:
        await autoplay_off(chat_id)
        await message.reply_text(
            "🔴 <b>AᴜᴛᴏPʟᴀʏ ᴍᴏᴅᴇ</b> ʙᴀɴᴅ ʜᴏ ɢᴀʏᴀ!\n\n"
            "ʙᴏᴛ ᴀʙ ǫᴜᴇᴜᴇ ᴋʜᴀᴛᴀᴍ ʜᴏɴᴇ ᴘᴀʀ ʀᴜᴋ ᴊᴀᴀʏᴇɢᴀ.\n\n"
            "ᴅᴏʙᴀʀᴀ ᴄʜᴀʟᴜ ᴋᴀʀɴᴇ ᴋᴇ ʟɪᴇ: /autoplay"
        )
    else:
        await autoplay_on(chat_id)
        await message.reply_text(
            "🟢 <b>AᴜᴛᴏPʟᴀʏ ᴍᴏᴅᴇ</b> ᴄʜᴀʟᴜ ʜᴏ ɢᴀʏᴀ! 🎵\n\n"
            "ᴀʙ ǫᴜᴇᴜᴇ ᴋʜᴀᴛᴀᴍ ʜᴏɴᴇ ᴋᴇ ʙᴀᴀᴅ ʙᴏᴛ ᴋʜᴜᴅ ʙᴇꜱᴛ ʙᴏʟʟʏᴡᴏᴏᴅ/ʟᴏᴠᴇ ꜱᴏɴɢꜱ ʙᴀᴊᴀᴛᴀ ʀʜᴇɢᴀ! 🤖\n\n"
            "❍ ʙᴀɴᴅ ᴋᴀʀɴᴇ ᴋᴇ ʟɪᴇ ᴅᴏʙᴀʀᴀ /autoplay ᴛʏᴘᴇ ᴋᴀʀᴏ."
        )


@app.on_message(
    filters.command(["autoplaysongs", "aplist"], prefixes=["/", "!", "."])
    & filters.group
    & ~BANNED_USERS
)
async def autoplay_songlist(client, message: Message):
    from RONALDO_MUSIC.core.call import _AUTOPLAY_POOL
    songs = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(_AUTOPLAY_POOL))
    await message.reply_text(
        f"🎵 <b>AᴜᴛᴏPʟᴀʏ ꜱᴏɴɢ Pᴏᴏʟ</b>\n\n"
        f"<code>{songs}</code>\n\n"
        f"ɪɴ ɪs ʟɪꜱᴛ ᴍᴇ ꜱᴇ ʀᴀɴᴅᴏᴍ ꜱᴏɴɢ ᴀᴜᴛᴏ ʙᴀᴊᴀʏᴀ ᴊᴀᴀᴇɢᴀ ᴊᴀʙ ǫᴜᴇᴜᴇ ᴋʜᴀᴛᴀᴍ ʜᴏ."
    )


__MODULE__ = "AᴜᴛᴏPʟᴀʏ"
__HELP__ = """
/autoplay — ǫᴜᴇᴜᴇ ᴋʜᴀᴛᴀᴍ ʜᴏɴᴇ ᴋᴇ ʙᴀᴀᴅ ʙᴏᴛ ᴋʜᴜᴅ ꜱᴏɴɢ ʙᴀᴊᴀɴᴀ ꜱʜᴜʀᴜ ᴋᴀʀᴇ (ᴛᴏɢɢʟᴇ)
/ap — ꜱᴀᴍᴇ ᴀꜱ /autoplay
/autoplaysongs — ᴀᴜᴛᴏᴘʟᴀʏ ꜱᴏɴɢ ʟɪꜱᴛ ᴅᴇᴋʜᴏ
"""
