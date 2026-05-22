import asyncio
import importlib
import time

from pyrogram import idle
from pyrogram.errors import FloodWait

import config
from RONALDO_MUSIC import LOGGER, app, userbot
from RONALDO_MUSIC.core.call import NOBITA
from RONALDO_MUSIC.misc import sudo
from RONALDO_MUSIC.plugins import ALL_MODULES
from RONALDO_MUSIC.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error(
            "𝐒𝐭𝐫𝐢𝐧𝐠 𝐒𝐞𝐬𝐬𝐢𝐨𝐧 𝐍𝐨𝐭 𝐅𝐢𝐥𝐥𝐞𝐝, 𝐏𝐥𝐞𝐚𝐬𝐞 𝐅𝐢𝐥𝐥 𝐀 𝐏𝐲𝐫𝐨𝐠𝐫𝐚𝐦 V2 𝐒𝐞𝐬𝐬𝐢𝐨𝐧🤬"
        )

    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except Exception:
        pass

    for attempt in range(5):
        try:
            await app.start()
            break
        except FloodWait as e:
            wait_sec = e.value + 5
            LOGGER(__name__).warning(
                f"Telegram FloodWait: waiting {wait_sec} seconds before retry (attempt {attempt + 1}/5)..."
            )
            await asyncio.sleep(wait_sec)
        except Exception as ex:
            LOGGER(__name__).error(f"Failed to start bot: {ex}")
            raise
    else:
        LOGGER(__name__).error("Failed to start bot after 5 FloodWait retries. Exiting.")
        return

    for all_module in ALL_MODULES:
        importlib.import_module("RONALDO_MUSIC.plugins" + all_module)
    LOGGER("RONALDO_MUSIC.plugins").info("𝐀𝐥𝐥 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬 𝐋𝐨𝐚𝐝𝐞𝐝 𝐁𝐚𝐛𝐲🥳...")
    await userbot.start()
    await NOBITA.start()
    await NOBITA.decorators()
    LOGGER("RONALDO_MUSIC").info(
        "╔═════ஜ۩۞۩ஜ════╗\n  ♨️𝗠𝗔𝗗𝗘 𝗕𝗬 ˹ 𝐑 𝐨 𝐧 𝛂 𝐥 𝐝 𝐨  ꧊𝆅  ❤️‍🔥♨️\n╚═════ஜ۩۞۩ஜ════╝"
    )
    await idle()
    await app.stop()
    await userbot.stop()
    LOGGER("RONALDO_MUSIC").info(
        "╔═════ஜ۩۞۩ஜ════╗\n  ♨️𝗠𝗔𝗗𝗘 𝗕𝗬 ˹ 𝐑 𝐨 𝐧 𝛂 𝐥 𝐝 𝐨  ꧊𝆅  ❤️‍🔥♨️\n╚═════ஜ۩۞۩ஜ════╝"
    )


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
