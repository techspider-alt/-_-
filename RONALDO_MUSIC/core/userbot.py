import asyncio
import httpx
from pyrogram.errors import FloodWait

import config
from ..logging import LOGGER

assistants = []
assistantids = []


def _send_to_logger(text: str):
    try:
        token = config.BOT_TOKEN
        chat_id = config.LOGGER_ID
        if not token or not chat_id:
            return
        httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception:
        pass


async def _start_assistant_tasks(client, number, logger_id):
    try:
        await client.join_chat("RONALDO_SUPPORT01")
    except Exception:
        pass

    assistants.append(number)

    try:
        client.id = client.me.id
        client.name = client.me.mention
        client.username = client.me.username
        assistantids.append(client.id)
        LOGGER(__name__).info(f"Assistant {number} started as {client.name}")
        _send_to_logger(
            f"<u><b>🎵 ᴀssɪsᴛᴀɴᴛ {number} sᴛᴀʀᴛᴇᴅ</b></u>\n\n"
            f"📛 <b>Name:</b> {client.name}\n"
            f"🆔 <b>ID:</b> <code>{client.id}</code>\n"
            f"👤 <b>Username:</b> @{client.username or 'N/A'}"
        )
    except Exception:
        pass


class Userbot:
    def __init__(self):
        self.one = None
        self.two = None
        self.three = None
        self.four = None
        self.five = None

    async def start(self):
        from RONALDO_MUSIC.core.call import RONALDO

        self.one   = RONALDO.userbot1
        self.two   = RONALDO.userbot2
        self.three = RONALDO.userbot3
        self.four  = RONALDO.userbot4
        self.five  = RONALDO.userbot5

        LOGGER(__name__).info("Starting Assistants (reusing Call clients)...")
        pairs = [
            (self.one,   1),
            (self.two,   2),
            (self.three, 3),
            (self.four,  4),
            (self.five,  5),
        ]
        for client, number in pairs:
            if client:
                await _start_assistant_tasks(client, number, config.LOGGER_ID)

        LOGGER(__name__).info(f"Active assistants: {assistants}")

    async def stop(self):
        LOGGER(__name__).info("Stopping Assistants...")
