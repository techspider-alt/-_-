import asyncio
import httpx
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

import config
from RONALDO_MUSIC import app


async def _send_to_logger(text: str):
    try:
        token = config.BOT_TOKEN
        chat_id = config.LOGGER_ID
        if not token or not chat_id:
            return
        async with httpx.AsyncClient(timeout=8) as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
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
            chat_title = "Private"
            chat_id_val = user.id if user else 0
            chat_info = "🔒 <b>Chat:</b> Private"
        else:
            chat_title = getattr(chat, "title", "Unknown")
            chat_id_val = chat.id
            chat_info = (
                f"👥 <b>Group:</b> {chat_title}\n"
                f"📌 <b>Chat ID:</b> <code>{chat.id}</code>"
            )

        if user:
            user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"
            username = f"@{user.username}" if user.username else "No username"
            user_info = (
                f"👤 <b>User:</b> {user_name} ({username})\n"
                f"🆔 <b>User ID:</b> <code>{user.id}</code>"
            )
            try:
                from RONALDO_MUSIC.utils.activity_tracker import record_command
                record_command(user_name, user.id, chat_title, chat_id_val, cmd_text)
            except Exception:
                pass
        else:
            user_info = "👤 <b>User:</b> Anonymous"

        log_text = (
            f"📩 <b>Command Used</b>\n\n"
            f"{user_info}\n"
            f"{chat_info}\n"
            f"💬 <b>Command:</b> <code>{cmd_text}</code>"
        )

        asyncio.create_task(_send_to_logger(log_text))
    except Exception:
        pass
