# =======================================================
# ©️ 2025-26 All Rights Reserved by RONALDO MUSIC 🚀
# This source code is under MIT License 📜
# 📩 DM for permission : @rchiex
# 🔗 Source : https://github.com/mystricman0-cell/DARK-MUSICS
# 📢 Telegram : https://t.me/rchiex
# =======================================================

import io
import os
import re
import aiohttp
import aiofiles
from RONALDO_MUSIC import app
from config import YOUTUBE_IMG_URL
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from youtubesearchpython.__future__ import VideosSearch

RONALDO_THUMB_URL = "https://files.catbox.moe/72kvx7.png"
_ronaldo_img_cache = None


def clear(text):
    return re.sub(r"\s+", " ", text).strip()


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(image.size[0] * min(widthRatio, heightRatio))
    newHeight = int(image.size[1] * min(widthRatio, heightRatio))
    return image.resize((newWidth, newHeight))


async def _get_ronaldo_img():
    """Download and cache the Ronaldo watermark image."""
    global _ronaldo_img_cache
    if _ronaldo_img_cache is not None:
        return _ronaldo_img_cache
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(RONALDO_THUMB_URL) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    img = Image.open(io.BytesIO(data)).convert("RGBA")
                    _ronaldo_img_cache = img
                    return img
    except Exception:
        pass
    return None


async def get_thumb(videoid):
    if os.path.isfile(f"cache/{videoid}.png"):
        return f"cache/{videoid}.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            try:
                title = result["title"]
                title = re.sub(r"\W+", " ", title)
                title = title.title()
            except Exception:
                title = "Unsupported Title"
            try:
                duration = result["duration"]
            except Exception:
                duration = "Unknown Mins"
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            try:
                views = result["viewCount"]["short"]
            except Exception:
                views = "Unknown Views"
            try:
                channel = result["channel"]["name"]
            except Exception:
                channel = "Unknown Channel"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(f"cache/thumb{videoid}.png", mode="wb")
                    await f.write(await resp.read())
                    await f.close()

        youtube = Image.open(f"cache/thumb{videoid}.png")
        youtube = youtube.convert("RGBA")

        background = youtube.resize((1280, 720)).filter(ImageFilter.GaussianBlur(radius=10))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)

        draw = ImageDraw.Draw(background)

        center_thumb_size = (942, 422)
        center_thumb = youtube.resize(center_thumb_size)

        border_size = 14
        bordered_center_thumb = Image.new(
            "RGBA",
            (center_thumb_size[0] + 2 * border_size, center_thumb_size[1] + 2 * border_size),
            (255, 255, 255),
        )
        bordered_center_thumb.paste(center_thumb, (border_size, border_size))

        pos_x = (1280 - bordered_center_thumb.size[0]) // 2
        pos_y = ((720 - bordered_center_thumb.size[1]) // 2) - 30
        background.paste(bordered_center_thumb, (pos_x, pos_y))

        arial = ImageFont.truetype("RONALDO_MUSIC/assets/font2.ttf", 30)
        font = ImageFont.truetype("RONALDO_MUSIC/assets/font.ttf", 30)
        bold_font = ImageFont.truetype("RONALDO_MUSIC/assets/font.ttf", 33)

        # ── Ronaldo watermark image (top-right corner) ──────────────────────
        ronaldo_img = await _get_ronaldo_img()
        if ronaldo_img:
            try:
                wm_size = (110, 110)
                wm = ronaldo_img.resize(wm_size, Image.LANCZOS)
                # Circular mask for clean look
                mask = Image.new("L", wm_size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, wm_size[0], wm_size[1]), fill=255)
                wm_circle = Image.new("RGBA", wm_size, (0, 0, 0, 0))
                wm_circle.paste(wm, mask=mask)
                bg_rgb = background.convert("RGBA")
                bg_rgb.paste(wm_circle, (1280 - wm_size[0] - 10, 10), mask=wm_circle)
                background = bg_rgb.convert("RGBA")
                draw = ImageDraw.Draw(background)
            except Exception:
                pass

        # ── Branding text (top-left) ─────────────────────────────────────────
        try:
            text_bbox = draw.textbbox((0, 0), "RONALDO MUSIC ❤️", font=font)
            text_w = text_bbox[2] - text_bbox[0]
        except AttributeError:
            text_w, _ = draw.textsize("RONALDO MUSIC ❤️", font=font)
        draw.text((10, 10), "RONALDO MUSIC ❤️", fill="yellow", font=font)

        # ── Channel & views ──────────────────────────────────────────────────
        draw.text(
            (55, 580),
            f"{channel} | {views[:23]}",
            (255, 255, 255),
            font=arial,
        )

        # ── Song title ───────────────────────────────────────────────────────
        draw.text(
            (57, 620),
            title[:60],
            (255, 255, 255),
            font=font,
        )

        # ── Playback bar ─────────────────────────────────────────────────────
        draw.text((55, 655), "00:00", fill="white", font=bold_font)
        start_x = 150
        end_x = 1130
        line_y = 670
        # Grey background line
        draw.line([(start_x, line_y), (end_x, line_y)], fill=(180, 180, 180, 200), width=4)
        # Glowing red played portion
        dot_x = start_x + 12
        draw.line([(start_x, line_y), (dot_x, line_y)], fill=(255, 50, 80), width=4)
        # Dot on the line
        dot_r = 9
        draw.ellipse(
            [(dot_x - dot_r, line_y - dot_r), (dot_x + dot_r, line_y + dot_r)],
            fill=(255, 50, 80),
            outline=(255, 255, 255),
        )
        # Stylish 𝗥𝗢𝗡𝗔𝗟𝗗𝗢 label above the dot
        ronaldo_label = "𝗥𝗢𝗡𝗔𝗟𝗗𝗢 ♫"
        try:
            lbl_bbox = draw.textbbox((0, 0), ronaldo_label, font=bold_font)
            lbl_w = lbl_bbox[2] - lbl_bbox[0]
        except AttributeError:
            lbl_w, _ = draw.textsize(ronaldo_label, font=bold_font)
        label_x = max(start_x, dot_x - lbl_w // 2)
        draw.text((label_x, 628), ronaldo_label, fill=(255, 50, 80), font=bold_font)
        try:
            dur_bbox = draw.textbbox((0, 0), duration, font=bold_font)
            dur_w = dur_bbox[2] - dur_bbox[0]
        except AttributeError:
            dur_w, _ = draw.textsize(duration, font=bold_font)
        draw.text((end_x + 10, 655), duration, fill="white", font=bold_font)

        try:
            os.remove(f"cache/thumb{videoid}.png")
        except Exception:
            pass

        background.save(f"cache/{videoid}.png")
        return f"cache/{videoid}.png"

    except Exception as e:
        print(f"[Thumbnail Error] {e}")
        return YOUTUBE_IMG_URL
