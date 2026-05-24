import os
import subprocess
import time

from pyrogram import filters

import config
from RONALDO_MUSIC import app
from RONALDO_MUSIC.misc import SUDOERS


@app.on_message(filters.command(["githubpush", "gpush"]) & SUDOERS)
async def github_push_cmd(_, message):
    m = await message.reply_text("🔄 <b>Pushing to GitHub...</b>")
    git_token = os.environ.get("GIT_TOKEN")
    branch = os.environ.get("UPSTREAM_BRANCH", "main")
    repo = os.environ.get("GITHUB_REPO", "mystricman0-cell/DARK-MUSICS")

    if not git_token:
        return await m.edit("❌ <b>GIT_TOKEN not set in secrets!</b>")
    if not repo:
        return await m.edit("❌ <b>GITHUB_REPO not set in secrets!</b>")

    remote_url = f"https://{git_token}@github.com/{repo}.git"
    subprocess.run(["git", "config", "user.email", "bot@ronaldomusic.replit"], capture_output=True)
    subprocess.run(["git", "config", "user.name", "RONALDO MUSIC Bot"], capture_output=True)
    subprocess.run(["git", "add", "-A"], capture_output=True)

    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if diff.returncode == 0:
        return await m.edit("✅ <b>Nothing to push — already up to date!</b>")

    commit_msg = f"Manual push by {message.from_user.first_name}: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True)

    result = subprocess.run(
        ["git", "push", remote_url, f"HEAD:{branch}"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        await m.edit(
            f"✅ <b>Successfully pushed to GitHub!</b>\n\n"
            f"📁 <b>Repo:</b> <code>{repo}</code>\n"
            f"🌿 <b>Branch:</b> <code>{branch}</code>\n"
            f"🕐 <b>Time:</b> <code>{time.strftime('%Y-%m-%d %H:%M:%S')}</code>"
        )
    else:
        await m.edit(f"❌ <b>Push failed!</b>\n\n<code>{result.stderr[:300]}</code>")
