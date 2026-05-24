import asyncio
from pyrogram.errors import FloodWait

import config
from ..logging import LOGGER

assistants = []
assistantids = []


async def _start_assistant_tasks(client, number, logger_id):
    """Run post-start tasks using an already-connected Pyrogram client."""
    try:
        await client.join_chat("RONALDO_SUPPORT01")
    except Exception:
        pass

    assistants.append(number)
    try:
        await client.send_message(logger_id, f"✅ Assistant {number} Started")
    except Exception:
        LOGGER(__name__).warning(
            f"Assistant {number}: Could not send message to log group."
        )
    try:
        client.id = client.me.id
        client.name = client.me.mention
        client.username = client.me.username
        assistantids.append(client.id)
        LOGGER(__name__).info(f"Assistant {number} started as {client.name}")
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
        """
        Use already-started Pyrogram clients from the RONALDO Call instance.
        This avoids AuthKeyDuplicated by never opening a second connection
        with the same session string.
        """
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
