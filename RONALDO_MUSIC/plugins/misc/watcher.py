from pyrogram import filters
from pyrogram.types import Message

from RONALDO_MUSIC import app
from RONALDO_MUSIC.core.call import RONALDO

welcome = 20
close = 30


@app.on_message(filters.video_chat_started, group=welcome)
@app.on_message(filters.video_chat_ended, group=close)
async def welcome(_, message: Message):
    await RONALDO.stop_stream_force(message.chat.id)
