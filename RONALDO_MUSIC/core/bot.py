import os
import httpx
from pyrogram import Client

import config
from ..logging import LOGGER

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sessions")
os.makedirs(SESSION_DIR, exist_ok=True)


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


class RONALDO(Client):
    def __init__(self):
        LOGGER(__name__).info(f"Starting Bot...")
        super().__init__(
            name="RONALDO_BOT",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            max_concurrent_transmissions=7,
        )

    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = f"@{self.username}"

        try:
            from RONALDO_MUSIC.utils.activity_tracker import set_bot_info
            set_bot_info(self.name, self.id, self.username)
        except Exception:
            pass

        _send_to_logger(
            f"<u><b>🤖 ʙᴏᴛ sᴛᴀʀᴛᴇᴅ</b></u>\n\n"
            f"📛 <b>Name:</b> {self.name}\n"
            f"🆔 <b>Bot ID:</b> <code>{self.id}</code>\n"
            f"👤 <b>Username:</b> @{self.username}"
        )

        LOGGER(__name__).info(f"Music Bot Started as {self.name}")

    async def stop(self):
        await super().stop()
