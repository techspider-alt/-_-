import asyncio

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import FloodWait

from RONALDO_MUSIC import app
from RONALDO_MUSIC.misc import SUDOERS
from RONALDO_MUSIC.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_served_chats,
    get_served_users,
)
from RONALDO_MUSIC.utils.decorators.language import language
from RONALDO_MUSIC.utils.formatters import alpha_to_int
from config import adminlist

IS_BROADCASTING = False

HELP_TEXT = (
    "╔══〔 📢 <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗛𝗘𝗟𝗣</b> 〕══╗\n\n"
    "<b>Usage:</b>\n"
    "  <code>/broadcast [text]</code>\n"
    "  <code>/broadcast</code> (reply to a message)\n\n"
    "<b>Flags:</b>\n"
    "  <code>-pin</code>       → Pin silently in all groups\n"
    "  <code>-pinloud</code>   → Pin with notification\n"
    "  <code>-nobot</code>     → Skip group broadcast\n"
    "  <code>-user</code>      → Broadcast to all users\n"
    "  <code>-assistant</code> → Broadcast via assistants\n\n"
    "<b>Examples:</b>\n"
    "  <code>/broadcast -pin Hello everyone!</code>\n"
    "  <code>/broadcast -pinloud -user Big update!</code>\n\n"
    "╚════════════════════════════╝"
)


def _mode_label(text: str) -> str:
    modes = []
    if "-pinloud" in text:
        modes.append("📌 Pin Loud")
    elif "-pin" in text:
        modes.append("📌 Pin Silent")
    if "-user" in text:
        modes.append("👤 Users")
    if "-assistant" in text:
        modes.append("🤖 Assistants")
    if "-nobot" not in text:
        modes.append("👥 Groups")
    return "  •  ".join(modes) if modes else "👥 Groups"


@app.on_message(
    filters.command(["broadcast", "gcast", "bcast"], prefixes=["/", "!", "."])
    & SUDOERS
)
@language
async def broadcast_message(client, message, _):
    global IS_BROADCASTING

    # ── Parse input ────────────────────────────────────────────────────────────
    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
        query = None
    else:
        if len(message.command) < 2:
            return await message.reply_text(HELP_TEXT)
        raw = message.text.split(None, 1)[1]
        query = raw
        for flag in ["-pin", "-pinloud", "-nobot", "-assistant", "-user"]:
            query = query.replace(flag, "")
        query = query.strip()
        if not query:
            return await message.reply_text(HELP_TEXT)
        x = y = None

    IS_BROADCASTING = True
    mode_str = _mode_label(message.text)

    status_msg = await message.reply_text(
        f"╔══〔 📢 <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧𝗜𝗡𝗚</b> 〕══╗\n\n"
        f"🔄 <b>Status :</b> Starting…\n"
        f"📡 <b>Modes :</b> {mode_str}\n\n"
        f"╚════════════════════════════╝"
    )

    total_sent = 0
    total_pin = 0
    total_users = 0
    total_ass = {}

    # ── GROUP BROADCAST ────────────────────────────────────────────────────────
    if "-nobot" not in message.text:
        sent = pin = 0
        chats = [int(c["chat_id"]) for c in await get_served_chats()]
        total_chats = len(chats)

        for idx, chat_id in enumerate(chats, 1):
            try:
                m = (
                    await app.forward_messages(chat_id, y, x)
                    if message.reply_to_message
                    else await app.send_message(chat_id, text=query)
                )
                if "-pinloud" in message.text:
                    try:
                        await m.pin(disable_notification=False)
                        pin += 1
                    except Exception:
                        pass
                elif "-pin" in message.text:
                    try:
                        await m.pin(disable_notification=True)
                        pin += 1
                    except Exception:
                        pass
                sent += 1
                await asyncio.sleep(0.2)

                # Live progress every 25 chats
                if idx % 25 == 0:
                    try:
                        await status_msg.edit_text(
                            f"╔══〔 📢 <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧𝗜𝗡𝗚</b> 〕══╗\n\n"
                            f"🔄 <b>Status :</b> Broadcasting to groups…\n"
                            f"📡 <b>Modes :</b> {mode_str}\n"
                            f"👥 <b>Progress :</b> {idx}/{total_chats} groups\n"
                            f"✅ <b>Sent :</b> {sent}  📌 <b>Pinned :</b> {pin}\n\n"
                            f"╚════════════════════════════╝"
                        )
                    except Exception:
                        pass

            except FloodWait as fw:
                wait = int(fw.value)
                if wait > 200:
                    continue
                await asyncio.sleep(wait)
            except Exception:
                continue

        total_sent = sent
        total_pin = pin

    # ── USER BROADCAST ─────────────────────────────────────────────────────────
    if "-user" in message.text:
        susr = 0
        users = [int(u["user_id"]) for u in await get_served_users()]
        total_u = len(users)

        try:
            await status_msg.edit_text(
                f"╔══〔 📢 <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧𝗜𝗡𝗚</b> 〕══╗\n\n"
                f"🔄 <b>Status :</b> Broadcasting to users…\n"
                f"📡 <b>Modes :</b> {mode_str}\n"
                f"👤 <b>Total users :</b> {total_u}\n\n"
                f"╚════════════════════════════╝"
            )
        except Exception:
            pass

        for user_id in users:
            try:
                (
                    await app.forward_messages(user_id, y, x)
                    if message.reply_to_message
                    else await app.send_message(user_id, text=query)
                )
                susr += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                wait = int(fw.value)
                if wait > 200:
                    continue
                await asyncio.sleep(wait)
            except Exception:
                pass

        total_users = susr

    # ── ASSISTANT BROADCAST ────────────────────────────────────────────────────
    if "-assistant" in message.text:
        from RONALDO_MUSIC.core.userbot import assistants

        try:
            await status_msg.edit_text(
                f"╔══〔 📢 <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧𝗜𝗡𝗚</b> 〕══╗\n\n"
                f"🔄 <b>Status :</b> Broadcasting via assistants…\n"
                f"📡 <b>Modes :</b> {mode_str}\n\n"
                f"╚════════════════════════════╝"
            )
        except Exception:
            pass

        for num in assistants:
            ass_sent = 0
            try:
                ass_client = await get_client(num)
                async for dialog in ass_client.get_dialogs():
                    try:
                        (
                            await ass_client.forward_messages(dialog.chat.id, y, x)
                            if message.reply_to_message
                            else await ass_client.send_message(dialog.chat.id, text=query)
                        )
                        ass_sent += 1
                        await asyncio.sleep(3)
                    except FloodWait as fw:
                        wait = int(fw.value)
                        if wait > 200:
                            continue
                        await asyncio.sleep(wait)
                    except Exception:
                        continue
            except Exception:
                pass
            total_ass[num] = ass_sent

    # ── FINAL RESULT CARD ──────────────────────────────────────────────────────
    IS_BROADCASTING = False

    ass_lines = ""
    if total_ass:
        for num, cnt in total_ass.items():
            ass_lines += f"  🤖 Assistant {num}: <code>{cnt}</code> chats\n"

    result_card = (
        f"╔══〔 ✅ <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘</b> 〕══╗\n\n"
        f"📡 <b>Modes :</b> {mode_str}\n\n"
    )

    if "-nobot" not in message.text:
        result_card += (
            f"👥 <b>Groups sent :</b> <code>{total_sent}</code>\n"
            f"📌 <b>Pinned :</b> <code>{total_pin}</code>\n"
        )
    if "-user" in message.text:
        result_card += f"👤 <b>Users sent :</b> <code>{total_users}</code>\n"
    if ass_lines:
        result_card += f"\n{ass_lines}"

    result_card += f"\n╚════════════════════════════╝"

    try:
        await status_msg.edit_text(result_card)
    except Exception:
        await message.reply_text(result_card)


# ── Auto admin-list refresh task ───────────────────────────────────────────────
async def auto_clean():
    while not await asyncio.sleep(10):
        try:
            served_chats = await get_active_chats()
            for chat_id in served_chats:
                if chat_id not in adminlist:
                    adminlist[chat_id] = []
                    async for user in app.get_chat_members(
                        chat_id, filter=ChatMembersFilter.ADMINISTRATORS
                    ):
                        if user.privileges.can_manage_video_chats:
                            adminlist[chat_id].append(user.user.id)
                    authusers = await get_authuser_names(chat_id)
                    for user in authusers:
                        user_id = await alpha_to_int(user)
                        adminlist[chat_id].append(user_id)
        except Exception:
            continue


asyncio.create_task(auto_clean())
