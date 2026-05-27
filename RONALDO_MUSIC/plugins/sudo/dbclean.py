import asyncio
from datetime import datetime

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from RONALDO_MUSIC import app
from RONALDO_MUSIC.core.mongo import mongodb
from RONALDO_MUSIC.utils.mongo import afkdb, coupledb, filtersdb, nightmodedb, notesdb
from config import BANNED_USERS, OWNER_IDS

# ── State ──────────────────────────────────────────────────────────────────────
_auto_clean_enabled = False
_auto_clean_task = None
AUTO_CLEAN_INTERVAL = 24 * 60 * 60  # 24 hours in seconds
_autodbclean_col = mongodb.autodbclean


def _owner_filter():
    return filters.user(OWNER_IDS)


# ── Core cleanup logic ─────────────────────────────────────────────────────────
async def _do_clean() -> dict:
    countdb      = mongodb.upcount
    connectdb    = mongodb.connect
    langdb       = mongodb.language
    playmodedb   = mongodb.playmode
    playtypedb   = mongodb.playtypedb
    playlistdb   = mongodb.playlist
    activechatdb = mongodb.activechats
    onoffdb      = mongodb.onoffper
    skipdb       = mongodb.skipmode
    autoenddb    = mongodb.autoend

    deleted = {}

    pairs = [
        # ── Empty/broken per-chat config docs ─────────────────────────────
        ("AFK entries",            afkdb,        {}),
        ("Empty playlists",        playlistdb,   {"notes": {}}),
        ("Stale upvote configs",   countdb,      {"mode": {"$lte": 0}}),
        ("Bad nightmode docs",     nightmodedb,  {"mode": {"$exists": False}}),
        ("Empty filter docs",      filtersdb,    {"filters": {}}),
        ("Empty note docs",        notesdb,      {"notes": {}}),
        ("Empty couple docs",      coupledb,     {"couple": {}}),
        ("Broken playmode docs",   playmodedb,   {"mode": {"$in": [None, ""]}}),
        ("Broken playtype docs",   playtypedb,   {"mode": {"$in": [None, ""]}}),
        ("Broken language docs",   langdb,       {"lang":  {"$in": [None, ""]}}),
        # ── Stale runtime / session docs ──────────────────────────────────
        ("Stale active chats",     activechatdb, {}),
        ("Stale onoff docs",       onoffdb,      {"mode": {"$in": [None, ""]}}),
        ("Stale skip-mode docs",   skipdb,       {"mode": {"$in": [None, ""]}}),
        ("Stale autoend docs",     autoenddb,    {"autoend": {"$in": [None, ""]}}),
        # ── Orphan connect docs (no chat_id) ──────────────────────────────
        ("Orphan connect docs",    connectdb,    {"chat_id": {"$exists": False}}),
    ]

    for label, col, query in pairs:
        try:
            r = await col.delete_many(query)
            deleted[label] = r.deleted_count
        except Exception:
            deleted[label] = 0

    return deleted


# ── Card builder ───────────────────────────────────────────────────────────────
def _build_card(deleted: dict, trigger: str, auto: bool = False) -> str:
    total = sum(deleted.values())
    lines = "".join(
        f"  {'🟢' if v > 0 else '⚪'} <b>{k}:</b> <code>{v}</code>\n"
        for k, v in deleted.items()
    )
    mode_tag = "🤖 <b>Auto-Clean</b>" if auto else f"👤 <b>By :</b> {trigger}"
    ts = datetime.now().strftime("%d %b %Y • %I:%M %p")
    return (
        f"╔══〔 🧹 <b>𝗠𝗢𝗡𝗚𝗢 𝗗𝗕 𝗖𝗟𝗘𝗔𝗡𝗘𝗗</b> 〕══╗\n\n"
        f"{lines}\n"
        f"🗑 <b>Total Removed :</b> <code>{total}</code> docs\n"
        f"{mode_tag}\n"
        f"🕐 <b>Time :</b> {ts}\n"
        f"💾 <b>Status :</b> MongoDB optimised ✅\n\n"
        f"╚════════════════════════════╝"
    )


# ── Auto-clean background loop ─────────────────────────────────────────────────
async def _auto_clean_loop():
    global _auto_clean_enabled
    while _auto_clean_enabled:
        await asyncio.sleep(AUTO_CLEAN_INTERVAL)
        if not _auto_clean_enabled:
            break
        try:
            deleted = await asyncio.wait_for(_do_clean(), timeout=60)
            card = _build_card(deleted, "Scheduler", auto=True)
            await app.send_message(
                config.LOGGER_ID,
                f"🤖 <b>Auto DB Clean triggered (every 24h)</b>\n\n{card}",
            )
        except Exception:
            pass


async def _load_auto_state():
    """Restore auto-clean state from MongoDB after bot restart."""
    global _auto_clean_enabled, _auto_clean_task
    doc = await _autodbclean_col.find_one({"_id": "autodbclean"})
    if doc and doc.get("enabled"):
        _auto_clean_enabled = True
        _auto_clean_task = asyncio.create_task(_auto_clean_loop())


# Load state on module import (runs inside event loop via plugin loader)
asyncio.get_event_loop().create_task(_load_auto_state())


# ── /dbclean — manual cleanup ──────────────────────────────────────────────────
@app.on_message(
    filters.command(["dbclean", "cleandb", "mongoclean", "dbflush"], prefixes=["/", "!", "."])
    & _owner_filter()
    & ~BANNED_USERS
)
async def db_clean_cmd(client, message: Message):
    msg = await message.reply_text(
        "🔄 <b>Scanning MongoDB for junk data…</b>\n<i>Please wait a moment.</i>"
    )
    try:
        deleted = await asyncio.wait_for(_do_clean(), timeout=30)
        card = _build_card(deleted, message.from_user.mention)
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✅ Done", callback_data="close_dbclean")]]
        )
        await msg.edit_text(card, reply_markup=btn)
    except asyncio.TimeoutError:
        await msg.edit_text("⚠️ Timeout — MongoDB may be slow. Try again.")
    except Exception as e:
        await msg.edit_text(f"❌ Error:\n<code>{e}</code>")


@app.on_callback_query(filters.regex("^close_dbclean$"))
async def close_dbclean_cb(client, cq):
    try:
        await cq.message.delete()
    except Exception:
        await cq.answer("Done!", show_alert=False)


# ── /autodbclean — toggle auto-clean every 24 h ────────────────────────────────
@app.on_message(
    filters.command(["autodbclean", "autocleandb", "schedclean"], prefixes=["/", "!", "."])
    & _owner_filter()
    & ~BANNED_USERS
)
async def auto_db_clean_cmd(client, message: Message):
    global _auto_clean_enabled, _auto_clean_task

    args = message.text.split()
    action = args[1].lower() if len(args) > 1 else None

    # Toggle if no arg given
    if action is None:
        action = "off" if _auto_clean_enabled else "on"

    if action == "on":
        if _auto_clean_enabled:
            return await message.reply_text(
                "✅ <b>Auto DB Clean is already <u>ON</u>.</b>\n"
                "🕐 Runs every <b>24 hours</b> automatically."
            )
        _auto_clean_enabled = True
        await _autodbclean_col.update_one(
            {"_id": "autodbclean"}, {"$set": {"enabled": True}}, upsert=True
        )
        if _auto_clean_task:
            _auto_clean_task.cancel()
        _auto_clean_task = asyncio.create_task(_auto_clean_loop())
        await message.reply_text(
            "╔══〔 🤖 <b>𝗔𝗨𝗧𝗢 𝗗𝗕 𝗖𝗟𝗘𝗔𝗡 𝗘𝗡𝗔𝗕𝗟𝗘𝗗</b> 〕══╗\n\n"
            "✅ Auto-clean is now <b>ON</b>\n"
            "🕐 Runs every <b>24 hours</b> silently\n"
            "📩 Report sent to <b>Logger group</b> after each run\n"
            "💡 Use <code>/autodbclean off</code> to disable\n\n"
            "╚══════════════════════════╝"
        )

    elif action == "off":
        if not _auto_clean_enabled:
            return await message.reply_text(
                "❌ <b>Auto DB Clean is already <u>OFF</u>.</b>\n"
                "Use <code>/autodbclean on</code> to enable."
            )
        _auto_clean_enabled = False
        await _autodbclean_col.update_one(
            {"_id": "autodbclean"}, {"$set": {"enabled": False}}, upsert=True
        )
        if _auto_clean_task:
            _auto_clean_task.cancel()
            _auto_clean_task = None
        await message.reply_text(
            "╔══〔 🛑 <b>𝗔𝗨𝗧𝗢 𝗗𝗕 𝗖𝗟𝗘𝗔𝗡 𝗗𝗜𝗦𝗔𝗕𝗟𝗘𝗗</b> 〕══╗\n\n"
            "❌ Auto-clean is now <b>OFF</b>\n"
            "💡 Use <code>/autodbclean on</code> to re-enable\n"
            "🧹 You can still run <code>/dbclean</code> manually\n\n"
            "╚══════════════════════════╝"
        )

    elif action == "status":
        state = "🟢 ON" if _auto_clean_enabled else "🔴 OFF"
        await message.reply_text(
            f"╔══〔 ℹ️ <b>Auto DB Clean Status</b> 〕══╗\n\n"
            f"📊 <b>Status :</b> {state}\n"
            f"🕐 <b>Interval :</b> Every 24 hours\n"
            f"📩 <b>Report to :</b> Logger group\n\n"
            f"╚══════════════════════════╝"
        )

    else:
        await message.reply_text(
            "❓ <b>Usage:</b>\n"
            "<code>/autodbclean on</code> — Enable auto-clean\n"
            "<code>/autodbclean off</code> — Disable auto-clean\n"
            "<code>/autodbclean status</code> — Check current status\n"
            "<code>/autodbclean</code> — Toggle on/off"
        )
