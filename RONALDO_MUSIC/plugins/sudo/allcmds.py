from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)

from RONALDO_MUSIC import app
from config import BANNED_USERS, OWNER_IDS

PAGES = {
    "music": {
        "title": "🎵 MUSIC COMMANDS",
        "cmds": [
            ("/play, /p", "Play audio in voice chat (YouTube/Spotify/SC/Apple)"),
            ("/vplay, /vp", "Play video in voice chat"),
            ("/cplay, /cvplay", "Play in connected channel"),
            ("/queue, /q", "Show current queue list"),
            ("/skip, /next", "Skip current song → auto-plays next"),
            ("/stop, /end", "Stop music (plays next if queue has songs)"),
            ("/pause, /cpause", "Pause current stream"),
            ("/resume, /cresume", "Resume paused stream"),
            ("/loop, /cloop", "Toggle loop (0 = off, number = times)"),
            ("/shuffle, /cshuffle", "Shuffle the queue"),
            ("/seek, /cseek", "Seek to a position e.g. /seek 1:30"),
            ("/seekback, /cseekback", "Seek backward"),
            ("/speed, /cspeed", "Change speed e.g. /speed 1.5"),
            ("/slow, /cslow", "Slow down speed"),
            ("/song", "Download a song as audio file"),
            ("/lyrics", "Get song lyrics"),
            ("/playback, /cplaying", "Show now playing info"),
        ],
    },
    "admin": {
        "title": "🛡 ADMIN COMMANDS",
        "cmds": [
            ("/auth", "Authorize user to use music in group"),
            ("/unauth", "Remove user auth"),
            ("/authlist", "List all authorized users"),
            ("/ban, /unban", "Ban/unban user from using bot in group"),
            ("/blchat, /unblchat", "Blacklist/whitelist a chat"),
            ("/blchats", "List blacklisted chats"),
            ("/setlang", "Set bot language for this group"),
            ("/setting, /settings", "Group bot settings"),
            ("/playmode", "Change play mode (Direct/Queue)"),
            ("/channelplay", "Enable/disable channel play mode"),
            ("/admincache", "Refresh admin cache"),
            ("/tagall, /atag", "Tag all members"),
            ("/mention", "Mention specific members"),
        ],
    },
    "sudo": {
        "title": "👑 SUDO / OWNER COMMANDS",
        "cmds": [
            ("/addsudo", "Add a sudo user (owner only)"),
            ("/delsudo, /rmsudo", "Remove sudo user"),
            ("/delallsudo", "Remove all sudo users"),
            ("/sudolist", "List all sudo users"),
            ("/broadcast", "Broadcast message to all groups"),
            ("/gcast", "Global cast to all chats"),
            ("/gban, /ungban", "Global ban/unban a user"),
            ("/gbanlist", "List all globally banned users"),
            ("/block, /unblock", "Block/unblock user from bot"),
            ("/blocked", "List blocked users"),
            ("/maintenance", "Toggle bot maintenance mode"),
            ("/restart, /reboot", "Restart the bot"),
            ("/logs, /get_log", "Get bot logs"),
            ("/eval, /sh", "Run Python/Shell code"),
            ("/autoend", "Toggle auto-end VC when empty"),
            ("/dbclean, /cleandb", "🧹 Clean MongoDB junk data"),
            ("/githubpush, /gpush", "Push code to GitHub manually"),
        ],
    },
    "tools": {
        "title": "🔧 TOOLS & FUN",
        "cmds": [
            ("/ping", "Check bot response time"),
            ("/stats, /gstats", "Bot usage statistics"),
            ("/tr", "Translate text e.g. /tr en Hello"),
            ("/font, /fonts", "Convert text to fancy fonts"),
            ("/qr", "Generate QR code from text"),
            ("/telegraph, /tgm", "Upload text/image to telegraph"),
            ("/shayari", "Random shayari"),
            ("/couples", "Find today's couple in group"),
            ("/afk, /brb", "Set AFK status"),
            ("/google, /g", "Search Google"),
            ("/ig", "Fetch Instagram post"),
            ("/quiz, /quizon, /quizoff", "Start/stop quiz game"),
            ("/mmf", "Add caption to meme image"),
            ("/kang, /st", "Steal/kang a sticker"),
            ("/stid", "Get sticker file ID"),
            ("/song", "Download audio from YouTube"),
            ("/tag, /tagall", "Tag group members"),
            ("/welcome", "Set welcome message"),
            ("/repo", "Get bot GitHub repo"),
        ],
    },
}

PAGE_ORDER = ["music", "admin", "sudo", "tools"]


def _build_text(page_key: str) -> str:
    page = PAGES[page_key]
    lines = ""
    for cmd, desc in page["cmds"]:
        lines += f"  ➤ <code>{cmd}</code>\n    <i>{desc}</i>\n\n"
    return (
        f"╔══〔 {page['title']} 〕══╗\n\n"
        f"{lines}"
        f"╚══════════════════════════════╝\n\n"
        f"<i>Use / prefix for all commands</i>"
    )


def _build_buttons(current: str) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton(
            ("▶ " if k == current else "") + PAGES[k]["title"].split(" ")[1],
            callback_data=f"allcmds_{k}",
        )
        for k in PAGE_ORDER[:2]
    ]
    row2 = [
        InlineKeyboardButton(
            ("▶ " if k == current else "") + PAGES[k]["title"].split(" ")[1],
            callback_data=f"allcmds_{k}",
        )
        for k in PAGE_ORDER[2:]
    ]
    row3 = [InlineKeyboardButton("✖ Close", callback_data="allcmds_close")]
    return InlineKeyboardMarkup([row1, row2, row3])


@app.on_message(
    filters.command(["cmds", "commands", "allcmds", "cmdlist"], prefixes=["/", "!", "."])
    & ~BANNED_USERS
)
async def all_commands(client, message: Message):
    page = "music"
    await message.reply_text(
        _build_text(page),
        reply_markup=_build_buttons(page),
        disable_web_page_preview=True,
    )


@app.on_callback_query(filters.regex(r"^allcmds_(.+)$"))
async def allcmds_cb(client, callback_query: CallbackQuery):
    key = callback_query.matches[0].group(1)
    if key == "close":
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        return
    if key not in PAGES:
        return await callback_query.answer("Unknown page.", show_alert=True)
    await callback_query.answer()
    await callback_query.message.edit_text(
        _build_text(key),
        reply_markup=_build_buttons(key),
        disable_web_page_preview=True,
    )
