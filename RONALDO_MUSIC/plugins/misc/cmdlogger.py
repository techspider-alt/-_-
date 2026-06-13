import asyncio
from datetime import datetime

import httpx
from pyrogram import filters
from pyrogram.types import Message

import config
from RONALDO_MUSIC import app

# ── Rate-limit: same user same chat max once per 8 sec ─────────────────────────
_cooldown: dict = {}
_COOLDOWN_SEC = 8

# ── Commands we skip (too noisy or internal) ───────────────────────────────────
_SKIP_CMDS = {"alive", "ping", "start"}


def _is_command(message: Message) -> bool:
    if not message.text:
        return False
    for prefix in ("/", "!", "."):
        if message.text.startswith(prefix) and len(message.text) > 1:
            return True
    return False


def _extract_command(text: str) -> str:
    word = text.split()[0].lstrip("/!.")
    return word.split("@")[0].lower()


def _build_log_card(
    cmd: str,
    user_name: str,
    user_id: int,
    group_name: str,
    chat_id: int,
    chat_type: str,
    full_text: str,
    ts: str,
) -> str:
    text_preview = full_text[:60] + ("…" if len(full_text) > 60 else "")
    chat_icon = "👥" if chat_type in ("group", "supergroup") else "👤"
    return (
        f"╔══〔 📋 <b>𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗟𝗢𝗚</b> 〕══╗\n\n"
        f"⚡ <b>Command :</b> <code>/{cmd}</code>\n"
        f"📝 <b>Full text :</b> <code>{text_preview}</code>\n\n"
        f"👤 <b>User :</b> {user_name}\n"
        f"🆔 <b>User ID :</b> <code>{user_id}</code>\n\n"
        f"{chat_icon} <b>{'Group' if chat_type in ('group','supergroup') else 'Chat'} :</b> {group_name}\n"
        f"🔑 <b>Chat ID :</b> <code>{chat_id}</code>\n\n"
        f"🕐 <b>Time :</b> {ts}\n\n"
        f"╚════════════════════════╝"
    )


async def _send_log(text: str):
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


@app.on_message(
    filters.create(lambda _, __, m: _is_command(m)),
    group=77,
)
async def command_logger(client, message: Message):
    try:
        cmd = _extract_command(message.text)

        if cmd in _SKIP_CMDS:
            return

        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id
        key = (user_id, chat_id)
        now = datetime.now().timestamp()
        last = _cooldown.get(key, 0)
        if now - last < _COOLDOWN_SEC:
            return
        _cooldown[key] = now

        user = message.from_user
        user_name = (
            f"{user.first_name}{(' ' + user.last_name) if user.last_name else ''}"
            if user else "Unknown"
        )
        user_mention = f"<a href='tg://user?id={user_id}'>{user_name}</a>"

        chat = message.chat
        group_name = getattr(chat, "title", None) or user_name
        chat_type = chat.type.name.lower() if chat.type else "unknown"

        ts = datetime.now().strftime("%d %b %Y  %I:%M:%S %p")

        card = _build_log_card(
            cmd=cmd,
            user_name=user_mention,
            user_id=user_id,
            group_name=group_name,
            chat_id=chat_id,
            chat_type=chat_type,
            full_text=message.text,
            ts=ts,
        )

        asyncio.create_task(_send_log(card))

    except Exception:
        pass
