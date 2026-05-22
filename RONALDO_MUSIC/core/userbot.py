import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait

import config

from ..logging import LOGGER

assistants = []
assistantids = []


def _make_assistant(name, session_string):
    """Create an assistant Client using session string (in-memory, no disk file)."""
    return Client(
        name=name,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=session_string,
        no_updates=True,
        in_memory=True,
    )


async def _start_assistant(client, number, logger_id):
    """Start one assistant with FloodWait handling and safe join."""
    for attempt in range(1, 6):
        try:
            await client.start()
            break
        except FloodWait as e:
            wait_sec = e.value + 5
            LOGGER(__name__).warning(
                f"Assistant {number} FloodWait: waiting {wait_sec}s (attempt {attempt}/5)..."
            )
            await asyncio.sleep(wait_sec)
        except Exception as ex:
            LOGGER(__name__).error(f"Assistant {number} failed to start: {ex}")
            return False

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
    return True


class Userbot(Client):
    def __init__(self):
        self.one   = _make_assistant("RONALDO_ASS1", str(config.STRING1)) if config.STRING1 else None
        self.two   = _make_assistant("RONALDO_ASS2", str(config.STRING2)) if config.STRING2 else None
        self.three = _make_assistant("RONALDO_ASS3", str(config.STRING3)) if config.STRING3 else None
        self.four  = _make_assistant("RONALDO_ASS4", str(config.STRING4)) if config.STRING4 else None
        self.five  = _make_assistant("RONALDO_ASS5", str(config.STRING5)) if config.STRING5 else None

    async def start(self):
        LOGGER(__name__).info("Starting Assistants...")
        if self.one:
            await _start_assistant(self.one, 1, config.LOGGER_ID)
        if self.two:
            await _start_assistant(self.two, 2, config.LOGGER_ID)
        if self.three:
            await _start_assistant(self.three, 3, config.LOGGER_ID)
        if self.four:
            await _start_assistant(self.four, 4, config.LOGGER_ID)
        if self.five:
            await _start_assistant(self.five, 5, config.LOGGER_ID)
        LOGGER(__name__).info(f"Active assistants: {assistants}")

    async def stop(self):
        LOGGER(__name__).info("Stopping Assistants...")
        for client, num in [
            (self.one, 1), (self.two, 2), (self.three, 3),
            (self.four, 4), (self.five, 5),
        ]:
            if client:
                try:
                    await client.stop()
                except Exception:
                    pass
