from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from RONALDO_MUSIC import app
from config import BOT_USERNAME
from RONALDO_MUSIC.utils.errors import capture_err
import httpx 
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

start_txt = """
✰ 𝗪ᴇʟᴄᴏᴍᴇ ᴛᴏ 𝗥ᴇᴘᴏs ✰
 
✰ 𝗥ᴇᴘᴏ ᴛᴏ 𝗡ʜɪ 𝗠ɪʟᴇɢᴀ 𝗬ʜᴀ
 
✰ 𝗣ᴀʜʟᴇ 𝗣ᴀᴘᴀ 𝗕ᴏʟ 𝗥ᴇᴘᴏ 𝗢ᴡɴᴇʀ ᴋᴏ 

✰ || @the1741 ||
 
✰ 𝗥ᴜɴ 24x7 𝗟ᴀɢ 𝗙ʀᴇᴇ 𝗪ɪᴛʜᴏᴜᴛ 𝗦ᴛᴏᴘ
 
"""




@app.on_message(filters.command("repo"))
async def start(_, msg):
    buttons = [
        [ 
          InlineKeyboardButton("𝗔ᴅᴅ ᴍᴇ 𝗠ᴀʙʏ", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
        ],
        [
          InlineKeyboardButton("𝗛ᴇʟᴘ", url="https://t.me/Ronaldo_X_supports"),
          InlineKeyboardButton("˹ 𝐑 𝐨 𝐧 𝛂 𝐥 𝐝 𝐨  ꧊𝆅  ❤️‍🔥", url="https://t.me/the1741"),
          ],
               [
                InlineKeyboardButton("˹ 𝐑 𝐨 𝐧 𝛂 𝐥 𝐝 𝐨  ꧊𝆅 ꭙ ꜱᴜᴘᴘᴏʀᴛ˼", url=f"https://t.me/Ronaldo_X_supports"),
],
[
InlineKeyboardButton("𝗢ᴡɴᴇʀ", url=f"https://t.me/the1741"),

        ]]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await msg.reply_photo(
        photo="https://files.catbox.moe/72kvx7.png",
        caption=start_txt,
        reply_markup=reply_markup
    )
