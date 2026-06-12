import asyncio
import httpx
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

import config
from RONALDO_MUSIC import app


def _log_to_telegram(text: str):
    try:
        token = config.BOT_TOKEN
        chat_id = config.LOGGER_ID
        if not token or not chat_id:
            return
        httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=8,
        )
    except Exception:
        pass


@app.on_message(filters.regex(r"^[/!]") & ~config.BANNED_USERS, group=-999)
async def command_log_handler(client, message: Message):
    try:
        user = message.from_user
        chat = message.chat
        cmd_text = (message.text or message.caption or "").split("\n")[0][:200]

        if chat.type == ChatType.PRIVATE:
            chat_info = f"🔒 <b>Private Chat</b>"
        else:
            chat_title = getattr(chat, "title", "Unknown")
            chat_info = f"👥 <b>Group:</b> {chat_title}\n📌 <b>Chat ID:</b> <code>{chat.id}</code>"

        if user:
            user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"
            username = f"@{user.username}" if user.username else "No username"
            user_info = (
                f"👤 <b>User:</b> {user_name} ({username})\n"
                f"🆔 <b>User ID:</b> <code>{user.id}</code>"
            )
        else:
            user_info = "👤 <b>User:</b> Anonymous"

        log_text = (
            f"📩 <b>Command Used</b>\n\n"
            f"{user_info}\n"
            f"{chat_info}\n"
            f"💬 <b>Command:</b> <code>{cmd_text}</code>"
        )

        asyncio.get_event_loop().run_in_executor(None, _log_to_telegram, log_text)
    except Exception:
        pass
