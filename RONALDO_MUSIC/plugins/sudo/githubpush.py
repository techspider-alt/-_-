import asyncio
import base64
import json
import os
import urllib.request
import urllib.error

from pyrogram import filters

from RONALDO_MUSIC import app
from RONALDO_MUSIC.misc import SUDOERS


def _gh_request(token, path, method="GET", data=None):
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data else None
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "RONALDO-MUSIC-BOT",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:300]}


def _get_sha(token, owner, repo, branch, path):
    r = _gh_request(token, f"/repos/{owner}/{repo}/contents/{path}?ref={branch}")
    return r.get("sha") if r and "sha" in r else None


def _push_file(token, owner, repo, branch, local_path, remote_path, message):
    try:
        with open(local_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None
    sha = _get_sha(token, owner, repo, branch, remote_path)
    payload = {"message": message, "content": content, "branch": branch}
    if sha:
        payload["sha"] = sha
    r = _gh_request(token, f"/repos/{owner}/{repo}/contents/{remote_path}", method="PUT", data=payload)
    return r


TRACKED_FILES = [
    "RONALDO_MUSIC/__main__.py",
    "RONALDO_MUSIC/core/call.py",
    "RONALDO_MUSIC/utils/stream/stream.py",
    "RONALDO_MUSIC/utils/stream/autoclear.py",
    "RONALDO_MUSIC/utils/database.py",
    "RONALDO_MUSIC/platforms/Youtube.py",
    "RONALDO_MUSIC/platforms/Spotify.py",
    "RONALDO_MUSIC/plugins/play/play.py",
    "RONALDO_MUSIC/plugins/play/autoplay.py",
    "RONALDO_MUSIC/plugins/play/radio.py",
    "RONALDO_MUSIC/plugins/play/live.py",
    "RONALDO_MUSIC/plugins/admins/skip.py",
    "RONALDO_MUSIC/plugins/admins/stop.py",
    "RONALDO_MUSIC/plugins/admins/callback.py",
    "RONALDO_MUSIC/plugins/misc/watcher.py",
    "RONALDO_MUSIC/plugins/misc/seeker.py",
    "RONALDO_MUSIC/plugins/sudo/dbclean.py",
    "RONALDO_MUSIC/plugins/sudo/allcmds.py",
    "RONALDO_MUSIC/plugins/sudo/githubpush.py",
    "RONALDO_MUSIC/plugins/tools/Gpt.py",
    "config.py",
    "requirements.txt",
    ".gitignore",
]


@app.on_message(filters.command(["githubpush", "gpush"]) & SUDOERS)
async def github_push_cmd(_, message):
    m = await message.reply_text("🔄 <b>Pushing to GitHub via API...</b>")

    git_token = os.environ.get("GIT_TOKEN", "")
    branch = os.environ.get("UPSTREAM_BRANCH", "main")
    repo_str = os.environ.get("GITHUB_REPO", "techspider-alt/-_-")

    if not git_token:
        return await m.edit("❌ <b>GIT_TOKEN not set in secrets!</b>")

    try:
        owner, repo = repo_str.split("/")
    except ValueError:
        return await m.edit("❌ <b>GITHUB_REPO format invalid (use owner/repo)</b>")

    import time
    commit_msg = f"Manual push by {message.from_user.first_name}: {time.strftime('%Y-%m-%d %H:%M:%S')}"

    loop = asyncio.get_running_loop()

    pushed = []
    failed = []
    skipped = []

    for fpath in TRACKED_FILES:
        if not os.path.exists(fpath):
            skipped.append(fpath)
            continue
        try:
            r = await loop.run_in_executor(
                None, _push_file, git_token, owner, repo, branch, fpath, fpath, commit_msg
            )
            if r and "content" in r:
                pushed.append(fpath)
            elif r and "error" in r:
                failed.append(f"{fpath}: {r['error'][:80]}")
            else:
                pushed.append(fpath)
        except Exception as e:
            failed.append(f"{fpath}: {e}")

    lines = [f"✅ <b>GitHub Push Complete!</b>\n"]
    if pushed:
        lines.append(f"<b>Pushed ({len(pushed)}):</b>")
        for f in pushed:
            lines.append(f"  • <code>{f}</code>")
    if skipped:
        lines.append(f"\n<b>Skipped (not found):</b> {len(skipped)}")
    if failed:
        lines.append(f"\n<b>Failed:</b>")
        for f in failed:
            lines.append(f"  • {f[:100]}")

    await m.edit("\n".join(lines))


__MODULE__ = "GɪᴛʜᴜʙPᴜꜱʜ"
__HELP__ = """
/githubpush — ᴘᴜꜱʜ ʙᴏᴛ ꜰɪʟᴇꜱ ᴛᴏ GɪᴛHᴜʙ ᴠɪᴀ API (ꜱᴜᴅᴏ ᴏɴʟʏ)
/gpush — ꜱᴀᴍᴇ ᴀꜱ /githubpush"""
