import asyncio
import time
import random
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from RONALDO_MUSIC import app
from RONALDO_MUSIC.misc import _boot_
from RONALDO_MUSIC.plugins.sudo.sudoers import sudoers_list
from RONALDO_MUSIC.utils.database import get_served_chats, get_served_users, get_sudoers
from RONALDO_MUSIC.utils import bot_sys_stats
from RONALDO_MUSIC.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from RONALDO_MUSIC.utils.decorators.language import LanguageStart
from RONALDO_MUSIC.utils.formatters import get_readable_time
from RONALDO_MUSIC.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string

RONALDO_VIDS = [
    config.START_VIDEO_URL,
] if config.START_VIDEO_URL else [
    "https://telegra.ph/file/1a3c152717eb9d2e94dc2.mp4",
    "https://files.catbox.moe/ln00jb.mp4",
    "https://graph.org/file/83ebf52e8bbf138620de7.mp4",
    "https://files.catbox.moe/0fq20c.mp4",
    "https://graph.org/file/318eac81e3d4667edcb77.mp4",
    "https://graph.org/file/7c1aa59649fbf3ab422da.mp4",
    "https://files.catbox.moe/t0nepm.mp4",
]

START_IMG = config.START_IMG_URL


async def _animated_send_start(message, caption, markup):
    """
    Full animated start sequence:
    1. Loading bar animation → delete
    2. Ping → Pong → delete
    3. Opening menu → delete
    4. Main menu with Ronaldo video
    """
    # Step 1 — Loading bar
    try:
        msg = await message.reply_text(
            "⚡ **ʀᴏɴᴀʟᴅᴏ ᴍᴜsɪᴄ** ɪs sᴛᴀʀᴛɪɴɢ...\n"
            "▓░░░░░░░░░ **10%**"
        )
        await asyncio.sleep(0.5)
        await msg.edit_text(
            "⚡ **ʀᴏɴᴀʟᴅᴏ ᴍᴜsɪᴄ** ɪs sᴛᴀʀᴛɪɴɢ...\n"
            "▓▓▓░░░░░░░ **30%**"
        )
        await asyncio.sleep(0.5)
        await msg.edit_text(
            "⚡ **ʀᴏɴᴀʟᴅᴏ ᴍᴜsɪᴄ** ɪs sᴛᴀʀᴛɪɴɢ...\n"
            "▓▓▓▓▓░░░░░ **50%**"
        )
        await asyncio.sleep(0.5)
        await msg.edit_text(
            "⚡ **ʀᴏɴᴀʟᴅᴏ ᴍᴜsɪᴄ** ɪs sᴛᴀʀᴛɪɴɢ...\n"
            "▓▓▓▓▓▓▓░░░ **70%**"
        )
        await asyncio.sleep(0.5)
        await msg.edit_text(
            "✅ **ʀᴏɴᴀʟᴅᴏ ᴍᴜsɪᴄ** ʀᴇᴀᴅʏ!\n"
            "▓▓▓▓▓▓▓▓▓▓ **100%**"
        )
        await asyncio.sleep(0.8)
        await msg.delete()
    except Exception:
        pass

    # Step 2 — Ping / Pong
    try:
        ping_msg = await message.reply_text(
            "🏓 **ᴘɪɴɢ...** ᴄʜᴇᴄᴋɪɴɢ ᴄᴏɴɴᴇᴄᴛɪᴏɴ..."
        )
        await asyncio.sleep(1.2)
        await ping_msg.edit_text(
            "🏓 **ᴘᴏɴɢ!** ᴄᴏɴɴᴇᴄᴛɪᴏɴ ᴏᴋ ✅"
        )
        await asyncio.sleep(1.0)
        await ping_msg.delete()
    except Exception:
        pass

    # Step 3 — Opening main menu
    try:
        menu_msg = await message.reply_text(
            "🎯 **ᴏᴘᴇɴɪɴɢ ᴍᴀɪɴ ᴍᴇɴᴜ...**\n"
            "⚡ ʟᴏᴀᴅɪɴɢ ʏᴏᴜʀ ᴇxᴘᴇʀɪᴇɴᴄᴇ..."
        )
        await asyncio.sleep(1.2)
        await menu_msg.delete()
    except Exception:
        pass

    # Step 4 — Main menu with video
    try:
        await message.reply_video(
            random.choice(RONALDO_VIDS),
            caption=caption,
            reply_markup=markup,
        )
    except Exception:
        try:
            await message.reply_photo(
                photo=START_IMG,
                caption=caption,
                reply_markup=markup,
            )
        except Exception:
            try:
                await message.reply_text(
                    text=caption,
                    reply_markup=markup,
                    disable_web_page_preview=True,
                )
            except Exception:
                pass


async def _send_start(message, caption, markup):
    """Simple send for group/welcome (no animation to avoid spam)."""
    try:
        await message.reply_video(
            random.choice(RONALDO_VIDS),
            caption=caption,
            reply_markup=markup,
        )
    except Exception:
        try:
            await message.reply_photo(
                photo=START_IMG,
                caption=caption,
                reply_markup=markup,
            )
        except Exception:
            try:
                await message.reply_text(
                    text=caption,
                    reply_markup=markup,
                    disable_web_page_preview=True,
                )
            except Exception:
                pass


async def _log_start(message, action):
    try:
        if await is_on_off(2):
            await app.send_message(
                chat_id=config.LOGGER_ID,
                text=f"{message.from_user.mention} {action}.\n\n"
                     f"<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n"
                     f"<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
            )
    except Exception:
        pass


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    try:
        await add_served_user(message.from_user.id)
    except Exception:
        pass

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        if name[0:4] == "help":
            try:
                keyboard = help_pannel(_)
                await _animated_send_start(
                    message,
                    _["help_1"].format(config.SUPPORT_CHAT),
                    keyboard,
                )
            except Exception:
                await message.reply_text(_["help_1"].format(config.SUPPORT_CHAT))
            return

        if name[0:3] == "sud":
            try:
                await sudoers_list(client=client, message=message, _=_)
            except Exception:
                pass
            await _log_start(message, "ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>")
            return

    out = private_panel(_)
    await _animated_send_start(
        message,
        _["start_2"].format(message.from_user.mention, app.mention),
        InlineKeyboardMarkup(out),
    )
    await _log_start(message, "ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ")


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    await _send_start(
        message,
        _["start_1"].format(app.mention, get_readable_time(uptime)),
        InlineKeyboardMarkup(out),
    )
    try:
        await add_served_chat(message.chat.id)
    except Exception:
        pass


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
        except Exception:
            _ = get_string("en")
        try:
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except Exception:
                    pass
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)
                try:
                    if message.chat.id in await blacklisted_chats():
                        await message.reply_text(
                            _["start_5"].format(
                                app.mention,
                                f"https://t.me/{app.username}?start=sudolist",
                                config.SUPPORT_CHAT,
                            ),
                            disable_web_page_preview=True,
                        )
                        return await app.leave_chat(message.chat.id)
                except Exception:
                    pass

                out = start_panel(_)
                await _send_start(
                    message,
                    _["start_3"].format(
                        message.from_user.mention if message.from_user else "User",
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    InlineKeyboardMarkup(out),
                )
                try:
                    await add_served_chat(message.chat.id)
                except Exception:
                    pass
        except Exception:
            pass
