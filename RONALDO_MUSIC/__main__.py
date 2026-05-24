import asyncio
import importlib
import os
import subprocess
import time

from aiohttp import web

# ── Patch ntgcalls/pytgcalls compatibility for ntgcalls 1.2.0 ─────────────
try:
    # 1. InputMode enum: Shell→SHELL, File→FILE
    from ntgcalls import InputMode as _IM
    if not hasattr(_IM, 'SHELL') and hasattr(_IM, 'Shell'):
        _IM.SHELL = _IM.Shell
    if not hasattr(_IM, 'FILE') and hasattr(_IM, 'File'):
        _IM.FILE = _IM.File
    if hasattr(_IM, 'SHELL') and not hasattr(_IM, 'Shell'):
        _IM.Shell = _IM.SHELL
    if hasattr(_IM, 'FILE') and not hasattr(_IM, 'File'):
        _IM.File = _IM.FILE
except Exception:
    pass

try:
    # 1b. StreamStatus enum: ntgcalls uses PLAYING/PAUSED/IDLING (uppercase)
    #     but pytgcalls internals reference Playing/Paused/Idling (titlecase).
    from ntgcalls import StreamStatus as _SS
    if hasattr(_SS, 'PLAYING') and not hasattr(_SS, 'Playing'):
        _SS.Playing = _SS.PLAYING
    if hasattr(_SS, 'PAUSED') and not hasattr(_SS, 'Paused'):
        _SS.Paused = _SS.PAUSED
    if hasattr(_SS, 'IDLING') and not hasattr(_SS, 'Idling'):
        _SS.Idling = _SS.IDLING
except Exception:
    pass

try:
    # 2. ToAsync: ntgcalls 1.2.x methods return asyncio.Future directly
    #    instead of blocking values. run_in_executor can't await a Future
    #    from a thread, so we patch _run on the class itself (not replace
    #    the class) so all already-imported references are also fixed.
    import asyncio as _asyncio
    import pytgcalls.to_async as _ta

    async def _patched_to_async_run(self):
        result = self._function(*self._function_args)
        if _asyncio.isfuture(result) or _asyncio.iscoroutine(result):
            return await result
        return result

    _ta.ToAsync._run = _patched_to_async_run
except Exception:
    pass

try:
    # 3. FFprobe -nostdin fix: ffprobe 7.1.1 does NOT support -nostdin flag.
    #    Patch build_command to only add -nostdin for ffmpeg, not ffprobe.
    import pytgcalls.ffmpeg as _ff

    _orig_build_command = _ff.build_command

    def _patched_build_command(name, ffmpeg_parameters, path, stream_parameters,
                               before_commands=None, headers=None, is_livestream=False):
        cmd = _orig_build_command(name, ffmpeg_parameters, path, stream_parameters,
                                  before_commands, headers, is_livestream)
        if name == 'ffprobe' and '-nostdin' in cmd:
            cmd = [c for c in cmd if c != '-nostdin']
        return cmd

    _ff.build_command = _patched_build_command
except Exception:
    pass
# ─────────────────────────────────────────────────────────────────────────

import httpx
from pyrogram import Client, idle
from pyrogram.errors import AuthKeyDuplicated, FloodWait

import config
from RONALDO_MUSIC import LOGGER, app, userbot
from RONALDO_MUSIC.core.call import RONALDO
from RONALDO_MUSIC.misc import sudo
from RONALDO_MUSIC.plugins import ALL_MODULES
from RONALDO_MUSIC.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def _health_handler(request):
    """Health check endpoint for Railway keep-alive."""
    return web.Response(text="OK", status=200)


async def _start_web_server():
    """Start a lightweight web server so Railway sees the service as alive."""
    port = int(os.environ.get("PORT", 8080))
    app_web = web.Application()
    app_web.router.add_get("/", _health_handler)
    app_web.router.add_get("/health", _health_handler)
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    LOGGER(__name__).info(f"💓 Heartbeat web server started on port {port}")


async def _heartbeat_loop():
    """Ping the health endpoint every 10 seconds to keep bot alive.
    Sends a Telegram notification to the logger group every 5 minutes."""
    import aiohttp
    port = int(os.environ.get("PORT", 8080))
    url = f"http://localhost:{port}/health"
    await asyncio.sleep(15)
    ping_count = 0
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        ping_count += 1
                        LOGGER(__name__).info(f"💓 Heartbeat OK — bot is alive! (ping #{ping_count})")
                        if ping_count % 30 == 0:
                            _tg_send(
                                f"💓 <b>RONALDO MUSIC — Heartbeat</b>\n\n"
                                f"✅ Bot is alive and running!\n"
                                f"🔢 Total pings: <code>{ping_count}</code>\n"
                                f"⏱ Uptime: ~{ping_count * 10 // 60} minutes"
                            )
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ Heartbeat ping failed: {e}")
        await asyncio.sleep(10)


async def _auto_push_github():
    """Push changes to GitHub every 20 seconds using GIT_TOKEN."""
    git_token = os.environ.get("GIT_TOKEN")
    branch = os.environ.get("UPSTREAM_BRANCH", "main")
    repo = os.environ.get("GITHUB_REPO", "mystricman0-cell/DARK-MUSICS")

    if not git_token:
        LOGGER(__name__).warning("GIT_TOKEN not set — auto-push disabled.")
        return

    if not repo:
        LOGGER(__name__).warning("GITHUB_REPO not set — auto-push disabled.")
        return

    remote_url = f"https://{git_token}@github.com/{repo}.git"

    subprocess.run(["git", "config", "user.email", "bot@ronaldomusic.replit"], capture_output=True)
    subprocess.run(["git", "config", "user.name", "RONALDO MUSIC Bot"], capture_output=True)

    LOGGER(__name__).info("🔄 Auto-push to GitHub started (every 20s).")

    while True:
        try:
            await asyncio.sleep(20)
            subprocess.run(["git", "add", "-A"], capture_output=True)
            diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
            if diff.returncode == 0:
                continue
            msg = f"Auto-push: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(["git", "commit", "-m", msg], capture_output=True)
            result = subprocess.run(
                ["git", "push", remote_url, f"HEAD:{branch}"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                LOGGER(__name__).info("✅ Auto-pushed to GitHub.")
            else:
                LOGGER(__name__).warning(f"⚠️ Auto-push failed: {result.stderr.strip()}")
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ Auto-push error: {e}")


def _tg_send(text: str):
    """Send a message to LOGGER_ID via raw HTTP — works even before Pyrogram starts."""
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


async def _validate_sessions():
    """
    Check each STRING_SESSION before the bot starts.
    - If AuthKeyDuplicated → alert logger + instruct user to regenerate
    - If any other error → warn but continue
    - If valid → proceed normally
    Returns True if at least one session is valid, False if all are bad.
    """
    strings = {
        "STRING_SESSION":  config.STRING1,
        "STRING_SESSION2": config.STRING2,
        "STRING_SESSION3": config.STRING3,
        "STRING_SESSION4": config.STRING4,
        "STRING_SESSION5": config.STRING5,
    }

    any_valid = False
    all_bad   = True

    for var_name, session_str in strings.items():
        if not session_str:
            continue

        LOGGER(__name__).info(f"🔍 Validating {var_name}...")
        test_client = Client(
            name=f"_validate_{var_name}",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=session_str,
            no_updates=True,
            in_memory=True,
        )
        try:
            await test_client.start()
            me = test_client.me
            LOGGER(__name__).info(
                f"✅ {var_name} is VALID — logged in as {me.first_name} (@{me.username})"
            )
            any_valid = True
            all_bad   = False
        except AuthKeyDuplicated:
            LOGGER(__name__).error(
                f"❌ {var_name} is INVALID — AuthKeyDuplicated! "
                f"Generate a new session from @StringFatherBot and update {var_name} in Railway."
            )
            _tg_send(
                f"❌ <b>RONALDO MUSIC — Session Invalid!</b>\n\n"
                f"⚠️ <code>{var_name}</code> has been invalidated by Telegram.\n\n"
                f"<b>Reason:</b> Same session was connected from 2 places simultaneously.\n\n"
                f"<b>Fix:</b>\n"
                f"1. Open @StringFatherBot on Telegram\n"
                f"2. Send /generate → choose Pyrogram V2\n"
                f"3. Enter your phone number + OTP\n"
                f"4. Copy the new session string\n"
                f"5. Replace <code>{var_name}</code> in Railway Variables\n"
                f"6. Redeploy\n\n"
                f"🤖 Bot will NOT start until this is fixed."
            )
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ {var_name} validation error: {type(e).__name__}: {e}")
        finally:
            try:
                await test_client.stop()
            except Exception:
                pass

    return not all_bad


async def _start_bot_with_retry(max_retries=15):
    """
    Start bot client, auto-waiting out any FloodWait.
    - Logs countdown to console every 30s
    - Sends Telegram notification to logger via raw HTTP
    - No crashes, no exit
    """
    for attempt in range(1, max_retries + 1):
        try:
            await app.start()
            LOGGER(__name__).info("✅ Bot client started successfully.")
            return True

        except FloodWait as e:
            wait_sec = int(e.value) + 5
            mins, secs = divmod(wait_sec, 60)

            LOGGER(__name__).warning(
                f"⏳ [FloodWait] Attempt {attempt}/{max_retries} — "
                f"waiting {wait_sec}s ({mins}m {secs}s)..."
            )

            # Notify logger group via direct HTTP (no Pyrogram needed)
            _tg_send(
                f"⏳ <b>RONALDO MUSIC — FloodWait</b>\n\n"
                f"Telegram rate limit encountered.\n"
                f"⏱ Waiting: <code>{wait_sec}s ({mins}m {secs}s)</code>\n"
                f"🔄 Attempt: {attempt}/{max_retries}\n"
                f"⚡ Bot will auto-start after wait..."
            )

            # Wait with countdown logs every 30s
            elapsed = 0
            while elapsed < wait_sec:
                chunk = min(30, wait_sec - elapsed)
                await asyncio.sleep(chunk)
                elapsed += chunk
                remaining = wait_sec - elapsed
                if remaining > 0:
                    r_m, r_s = divmod(remaining, 60)
                    LOGGER(__name__).info(
                        f"⏳ FloodWait: {remaining}s remaining ({r_m}m {r_s}s)..."
                    )

        except Exception as ex:
            LOGGER(__name__).error(f"Bot start failed: {type(ex).__name__}: {ex}")
            raise

    LOGGER(__name__).error("Bot failed to start after all retries.")
    _tg_send("❌ <b>RONALDO MUSIC</b> — Bot failed to start after all retries!")
    return False


async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error(
            "String Session Not Set — please fill a Pyrogram V2 session!"
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

    sessions_ok = await _validate_sessions()
    if not sessions_ok:
        LOGGER(__name__).error(
            "❌ All STRING_SESSION values are invalid! "
            "Please regenerate from @StringFatherBot and update Railway variables."
        )
        return

    started = await _start_bot_with_retry()
    if not started:
        return

    for all_module in ALL_MODULES:
        importlib.import_module("RONALDO_MUSIC.plugins" + all_module)
    LOGGER("RONALDO_MUSIC.plugins").info("𝐀𝐥𝐥 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬 𝐋𝐨𝐚𝐝𝐞𝐝 𝐁𝐚𝐛𝐲🥳...")

    await RONALDO.start()
    await userbot.start()
    await RONALDO.decorators()

    asyncio.get_event_loop().create_task(_auto_push_github())
    await _start_web_server()
    asyncio.get_event_loop().create_task(_heartbeat_loop())

    LOGGER("RONALDO_MUSIC").info(
        "╔═════ஜ۩۞۩ஜ════╗\n"
        "  ♨️ 𝗠𝗔𝗗𝗘 𝗕𝗬 ˹ 𝐑 𝐨 𝐧 𝛂 𝐥 𝐝 𝐨  ꧊𝆅  ❤️‍🔥 ♨️\n"
        "╚═════ஜ۩۞۩ஜ════╝"
    )
    await idle()
    await app.stop()
    await userbot.stop()
    LOGGER("RONALDO_MUSIC").info("Bot stopped gracefully.")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
