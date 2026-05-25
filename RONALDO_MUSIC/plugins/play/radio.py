import asyncio

from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from RONALDO_MUSIC import app
from RONALDO_MUSIC.core.call import RONALDO
from RONALDO_MUSIC.misc import db
from RONALDO_MUSIC.utils.database import (
    add_active_chat,
    get_assistant,
    get_lang,
    is_active_chat,
    music_on,
)
from RONALDO_MUSIC.utils.exceptions import AssistantErr
from RONALDO_MUSIC.utils.stream.queue import put_queue
from config import BANNED_USERS
from strings import get_string


RADIO_STATIONS = {
    "🇮🇳 Radio Mirchi 98.3": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio040/playlist.m3u8",
    "🇮🇳 AIR National (Hindi)": "https://air.pc.cdn.bitgravity.com/air/live/pbnationalhindi/playlist.m3u8",
    "🇮🇳 AIR FM Gold": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio001/playlist.m3u8",
    "🇮🇳 AIR FM Rainbow": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio002/playlist.m3u8",
    "🌍 BBC Hindi": "http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/nonuk/sbr_low/ak/bbc_hindi_radio.m3u8",
    "🌍 BBC World": "http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/nonuk/sbr_low/ak/bbc_world_service.m3u8",
    "🎵 Lofi Hip-Hop": "http://streams.ilovemusic.de/iloveradio17.mp3",
    "🎵 Chillout Radio": "http://streams.ilovemusic.de/iloveradio2.mp3",
    "🎵 Jazz FM": "http://streams.ilovemusic.de/iloveradio27.mp3",
}


def _radio_markup():
    buttons = []
    stations = list(RADIO_STATIONS.items())
    for i in range(0, len(stations), 2):
        row = []
        row.append(InlineKeyboardButton(
            stations[i][0], callback_data=f"radio_{i}"
        ))
        if i + 1 < len(stations):
            row.append(InlineKeyboardButton(
                stations[i + 1][0], callback_data=f"radio_{i+1}"
            ))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ ᴄʟᴏꜱᴇ", callback_data="radio_close")])
    return InlineKeyboardMarkup(buttons)


@app.on_message(
    filters.command(["radio", "radiostation", "radiostations"], prefixes=["/", "!", "."])
    & filters.group
    & ~BANNED_USERS
)
async def radio_command(client, message: Message):
    language = await get_lang(message.chat.id)
    _ = get_string(language)

    markup = _radio_markup()
    await message.reply_text(
        "📻 <b>RONALDO MUSIC — LIVE RADIO STATIONS</b>\n\n"
        "ɴᴇᴛ ʜɪᴛ ᴀɴʏ ʀᴀᴅɪᴏ ꜱᴛᴀᴛɪᴏɴ ᴛᴏ ꜱᴛᴀʀᴛ ꜱᴛʀᴇᴀᴍɪɴɢ ʟɪᴠᴇ 🔴\n\n"
        "ᴛʜᴇꜱᴇ ᴀʀᴇ ʟɪᴠᴇ ꜱᴛʀᴇᴀᴍꜱ — ɴᴏ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴇᴇᴅᴇᴅ!",
        reply_markup=markup,
    )


@app.on_callback_query(filters.regex(r"^radio_(\d+|close)$"))
async def radio_callback(client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id

    if data == "radio_close":
        await callback.message.delete()
        return

    try:
        idx = int(data.split("_")[1])
    except (ValueError, IndexError):
        return await callback.answer("❍ ɪɴᴠᴀʟɪᴅ ꜱᴛᴀᴛɪᴏɴ.", show_alert=True)

    stations = list(RADIO_STATIONS.items())
    if idx >= len(stations):
        return await callback.answer("❍ ꜱᴛᴀᴛɪᴏɴ ɴᴏᴛ ꜰᴏᴜɴᴅ.", show_alert=True)

    station_name, stream_url = stations[idx]
    language = await get_lang(chat_id)
    _ = get_string(language)

    await callback.answer(f"📻 ꜱᴛᴀʀᴛɪɴɢ {station_name}...", show_alert=False)

    user_name = callback.from_user.first_name
    user_id = callback.from_user.id
    original_chat_id = chat_id

    msg = await callback.message.reply_text(
        f"📻 ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ <b>{station_name}</b>...\n\nᴘʟᴇᴀsᴇ ᴡᴀɪᴛ..."
    )

    try:
        if await is_active_chat(chat_id):
            # Already playing — add to queue
            await put_queue(
                chat_id,
                original_chat_id,
                "index_url",
                station_name,
                "♾ Live",
                user_name,
                stream_url,
                user_id,
                "audio",
            )
            position = len(db.get(chat_id, []))
            await msg.edit(
                f"📻 <b>{station_name}</b> ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ ᴀᴛ ᴘᴏꜱɪᴛɪᴏɴ #{position}.\n\n"
                f"<b>ʙʏ:</b> {user_name}"
            )
        else:
            db[chat_id] = []
            await RONALDO.join_call(
                chat_id,
                original_chat_id,
                stream_url,
                video=None,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                "index_url",
                station_name,
                "♾ Live",
                user_name,
                stream_url,
                user_id,
                "audio",
            )
            db[chat_id][0]["mystic"] = msg
            db[chat_id][0]["markup"] = "tg"
            await msg.edit(
                f"📻 <b>ɴᴏᴡ ꜱᴛʀᴇᴀᴍɪɴɢ</b>\n\n"
                f"🔴 <b>{station_name}</b>\n\n"
                f"<b>ᴛʏᴘᴇ:</b> ʟɪᴠᴇ ʀᴀᴅɪᴏ\n"
                f"<b>ʀᴇǫᴜᴇꜱᴛᴇᴅ ʙʏ:</b> {user_name}\n\n"
                f"ᴜꜱᴇ /stop ᴛᴏ ꜱᴛᴏᴘ ᴏʀ /skip ᴛᴏ ꜱᴋɪᴘ."
            )
    except AssistantErr as e:
        await msg.edit(str(e))
    except Exception as e:
        await msg.edit(
            f"❍ ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴛᴀʀᴛ ʀᴀᴅɪᴏ.\n\n"
            f"<b>ᴇʀʀᴏʀ:</b> <code>{type(e).__name__}: {e}</code>"
        )
