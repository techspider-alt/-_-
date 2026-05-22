import os

from pyrogram import Client, filters
from pyrogram.errors import ChatAdminRequired, ChatWriteForbidden, UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from RONALDO_MUSIC import app
import config

MUST_JOIN = os.getenv("MUST_JOIN", None)


@app.on_message(filters.incoming & filters.private, group=-1)
async def must_join_channel(client: Client, msg: Message):
    if not MUST_JOIN:
        return
    if not msg.from_user:
        return
    try:
        try:
            await app.get_chat_member(MUST_JOIN, msg.from_user.id)
        except UserNotParticipant:
            try:
                chat_info = await app.get_chat(MUST_JOIN)
                link = chat_info.invite_link or f"https://t.me/{MUST_JOIN.lstrip('@')}"
            except Exception:
                link = f"https://t.me/{MUST_JOIN.lstrip('@')}"
            try:
                await msg.reply_text(
                    f"❍ Please join our support channel to use this bot!\n\n"
                    f"After joining, send your command again.",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("• ᴊᴏɪɴ •", url=link)]]
                    ),
                )
                await msg.stop_propagation()
            except ChatWriteForbidden:
                pass
    except ChatAdminRequired:
        pass
    except Exception:
        pass
