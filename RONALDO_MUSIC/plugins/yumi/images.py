import os
import re
import io
import asyncio
from re import findall

import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, Message

from RONALDO_MUSIC import app
from config import BANNED_USERS

_DDG_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


async def _ddg_images(query: str, limit: int = 6) -> list[str]:
    """Search DuckDuckGo for images. Returns list of image URLs."""
    try:
        async with aiohttp.ClientSession(headers=_DDG_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(
                "https://duckduckgo.com/",
                params={"q": query, "ia": "images"},
            ) as r:
                html = await r.text()

            vqd_match = re.search(r'vqd=["\']([\d-]+)["\']', html)
            if not vqd_match:
                vqd_match = re.search(r"vqd=([\d-]+)", html)
            if not vqd_match:
                return []
            vqd = vqd_match.group(1)

            async with session.get(
                "https://duckduckgo.com/i.js",
                params={"q": query, "vqd": vqd, "o": "json", "p": "1", "f": ",,,,,", "l": "us-en"},
            ) as r:
                data = await r.json(content_type=None)

            results = data.get("results", [])
            return [item["image"] for item in results[:limit] if item.get("image")]
    except Exception:
        return []


async def _download_img(session: aiohttp.ClientSession, url: str, idx: int) -> str | None:
    """Download an image to /tmp and return the file path."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
            if r.status != 200:
                return None
            data = await r.read()
        ext = url.split(".")[-1].split("?")[0].lower()
        if ext not in ("jpg", "jpeg", "png", "webp"):
            ext = "jpg"
        path = f"/tmp/imgdl_{idx}.{ext}"
        with open(path, "wb") as f:
            f.write(data)
        return path
    except Exception:
        return None


@app.on_message(filters.command(["img", "image"], prefixes=["/", "!"]) & ~BANNED_USERS)
async def google_img_search(client: Client, message: Message):
    chat_id = message.chat.id

    try:
        query = message.text.split(None, 1)[1].strip()
    except IndexError:
        return await message.reply("❍ ᴘʀᴏᴠɪᴅᴇ ᴀɴ ɪᴍᴀɢᴇ ǫᴜᴇʀʏ!\n\nExample: `/img cute cats`")

    lim_match = findall(r"lim=(\d+)", query)
    if lim_match:
        lim = min(int(lim_match[0]), 10)
        query = re.sub(r"lim=\d+", "", query).strip()
    else:
        lim = 6

    msg = await message.reply("🔍 **Searching for images...**")

    urls = await _ddg_images(query, lim)
    if not urls:
        return await msg.edit("❌ **No images found.** Try a different query.")

    await msg.edit(f"⬇️ **Downloading {len(urls)} images...**")

    downloaded = []
    async with aiohttp.ClientSession(headers=_DDG_HEADERS) as session:
        tasks = [_download_img(session, url, i) for i, url in enumerate(urls)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, str) and r and os.path.exists(r):
                downloaded.append(r)

    if not downloaded:
        return await msg.edit("❌ **Failed to download images.** Try a different query.")

    try:
        media = [InputMediaPhoto(media=p) for p in downloaded]
        await app.send_media_group(chat_id=chat_id, media=media, reply_to_message_id=message.id)
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ Error sending images: `{e}`")
    finally:
        for p in downloaded:
            try:
                os.remove(p)
            except Exception:
                pass
