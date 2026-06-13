import asyncio

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    PeerIdInvalid,
    UserIsBlocked,
)

import config
from RONALDO_MUSIC import app
from RONALDO_MUSIC.misc import SUDOERS
from RONALDO_MUSIC.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_served_chats,
    get_served_users,
)
from RONALDO_MUSIC.utils.formatters import alpha_to_int
from config import adminlist

IS_BROADCASTING = False

# ── Owner-only filter ──────────────────────────────────────────────────────────
_OWNER_FILTER = filters.user(config.OWNER_IDS)

HELP_TEXT = (
    "╔══〔 📢 <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗛𝗘𝗟𝗣</b> 〕══╗\n\n"
    "<b>Default (no flags):</b>\n"
    "  • Sends to ALL groups the bot is in\n"
    "  • Sends to ALL users' personal DMs\n"
    "  • Auto-pins in groups where bot is admin\n\n"
    "<b>Flags (optional):</b>\n"
    "  <code>-nogroup</code>  → Skip group broadcast\n"
    "  <code>-nouser</code>   → Skip user DM broadcast\n"
    "  <code>-nopin</code>    → Disable auto-pin even if admin\n"
    "  <code>-pinloud</code>  → Pin with notification (default: silent)\n\n"
    "<b>Examples:</b>\n"
    "  <code>/broadcast Hello everyone!</code>\n"
    "  <code>/broadcast -nopin Update message</code>\n"
    "  <code>/broadcast -pinloud -nouser Important!</code>\n\n"
    "╚════════════════════════════╝"
)


@app.on_message(
    filters.command(["broadcast", "gcast", "bcast"], prefixes=["/", "!", "."])
    & _OWNER_FILTER
)
async def broadcast_message(client, message):
    global IS_BROADCASTING

    # ── Parse input ────────────────────────────────────────────────────────
    if message.reply_to_message:
        reply_msg_id = message.reply_to_message.id
        reply_chat_id = message.chat.id
        query = None
    else:
        if len(message.command) < 2:
            return await message.reply_text(HELP_TEXT)
        raw = message.text.split(None, 1)[1]
        query = raw
        for flag in ["-nogroup", "-nouser", "-nopin", "-pinloud"]:
            query = query.replace(flag, "")
        query = query.strip()
        if not query:
            return await message.reply_text(HELP_TEXT)
        reply_msg_id = reply_chat_id = None

    txt = message.text or ""
    skip_groups = "-nogroup" in txt
    skip_users  = "-nouser"  in txt
    skip_pin    = "-nopin"   in txt
    loud_pin    = "-pinloud" in txt

    IS_BROADCASTING = True
    modes = []
    if not skip_groups:
        modes.append("👥 Groups (auto-pin where admin)")
    if not skip_users:
        modes.append("👤 Users DM")
    mode_str = "  •  ".join(modes) or "None"

    status_msg = await message.reply_text(
        f"╔══〔 📢 <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧𝗜𝗡𝗚</b> 〕══╗\n\n"
        f"🔄 <b>Status:</b> Starting…\n"
        f"📡 <b>Targets:</b> {mode_str}\n\n"
        f"╚════════════════════════════╝"
    )

    # ── GROUP BROADCAST ────────────────────────────────────────────────────
    grp_sent = grp_fail = grp_pin = 0
    if not skip_groups:
        chats = [int(c["chat_id"]) for c in await get_served_chats()]
        total = len(chats)
        for idx, chat_id in enumerate(chats, 1):
            try:
                m = (
                    await app.forward_messages(chat_id, reply_chat_id, reply_msg_id)
                    if reply_msg_id
                    else await app.send_message(chat_id, text=query)
                )
                grp_sent += 1
                # Try to auto-pin silently — succeeds only where bot is admin
                if not skip_pin:
                    try:
                        await m.pin(disable_notification=not loud_pin)
                        grp_pin += 1
                    except Exception:
                        pass
                await asyncio.sleep(0.2)
                if idx % 20 == 0 or idx == total:
                    try:
                        await status_msg.edit_text(
                            f"╔══〔 📢 <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧𝗜𝗡𝗚</b> 〕══╗\n\n"
                            f"👥 <b>Groups:</b> {idx}/{total}\n"
                            f"✅ Sent: <code>{grp_sent}</code>  "
                            f"📌 Pinned: <code>{grp_pin}</code>  "
                            f"❌ Failed: <code>{grp_fail}</code>\n\n"
                            f"╚════════════════════════════╝"
                        )
                    except Exception:
                        pass
            except FloodWait as fw:
                wait = int(fw.value)
                if wait <= 200:
                    await asyncio.sleep(wait)
                    try:
                        m = (
                            await app.forward_messages(chat_id, reply_chat_id, reply_msg_id)
                            if reply_msg_id
                            else await app.send_message(chat_id, text=query)
                        )
                        grp_sent += 1
                    except Exception:
                        grp_fail += 1
            except Exception:
                grp_fail += 1
                continue

    # ── USER DM BROADCAST ──────────────────────────────────────────────────
    usr_sent = usr_fail = 0
    if not skip_users:
        users = [int(u["user_id"]) for u in await get_served_users()]
        total_u = len(users)
        try:
            await status_msg.edit_text(
                f"╔══〔 📢 <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧𝗜𝗡𝗚</b> 〕══╗\n\n"
                f"👥 Groups done: <code>{grp_sent}</code> sent, <code>{grp_pin}</code> pinned\n"
                f"👤 <b>Now sending DMs to {total_u} users…</b>\n\n"
                f"╚════════════════════════════╝"
            )
        except Exception:
            pass

        for idx, user_id in enumerate(users, 1):
            try:
                (
                    await app.forward_messages(user_id, reply_chat_id, reply_msg_id)
                    if reply_msg_id
                    else await app.send_message(user_id, text=query)
                )
                usr_sent += 1
                await asyncio.sleep(0.1)
            except FloodWait as fw:
                wait = int(fw.value)
                if wait <= 200:
                    await asyncio.sleep(wait)
            except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid):
                usr_fail += 1
            except Exception:
                usr_fail += 1
            if idx % 50 == 0:
                try:
                    await status_msg.edit_text(
                        f"╔══〔 📢 <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧𝗜𝗡𝗚</b> 〕══╗\n\n"
                        f"👤 <b>Users DM:</b> {idx}/{total_u}\n"
                        f"✅ Sent: <code>{usr_sent}</code>  ❌ Failed: <code>{usr_fail}</code>\n\n"
                        f"╚════════════════════════════╝"
                    )
                except Exception:
                    pass

    IS_BROADCASTING = False

    # ── FINAL RESULT CARD ──────────────────────────────────────────────────
    result = "╔══〔 ✅ <b>𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗗𝗢𝗡𝗘</b> 〕══╗\n\n"
    if not skip_groups:
        result += (
            f"👥 <b>Groups:</b> ✅ <code>{grp_sent}</code> sent"
            f"  📌 <code>{grp_pin}</code> pinned"
            f"  ❌ <code>{grp_fail}</code> failed\n"
        )
    if not skip_users:
        result += (
            f"👤 <b>Users DM:</b> ✅ <code>{usr_sent}</code> sent"
            f"  ❌ <code>{usr_fail}</code> failed\n"
        )
    result += "\n╚════════════════════════════╝"

    try:
        await status_msg.edit_text(result)
    except Exception:
        await message.reply_text(result)

    # ── Send full report to every owner's DM ──────────────────────────────
    owner_report = (
        f"📢 <b>Broadcast Report</b>\n\n"
        f"👤 <b>Triggered by:</b> {message.from_user.mention} "
        f"(<code>{message.from_user.id}</code>)\n"
        f"🏠 <b>From chat:</b> {getattr(message.chat, 'title', 'Private')}\n\n"
        + result
    )
    for owner_id in config.OWNER_IDS:
        try:
            # Skip if message was already sent in owner's own DM
            if message.chat.id == owner_id:
                continue
            await app.send_message(owner_id, owner_report)
        except Exception:
            pass


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
