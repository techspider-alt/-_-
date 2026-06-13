import re
import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.raw.functions.phone import CreateGroupCall, DiscardGroupCall
from RONALDO_MUSIC import app
from config import OWNER_ID, BANNED_USERS


# VC started notification
@app.on_message(filters.video_chat_started)
async def vc_started(_, msg):
    await msg.reply("**😍 ᴠɪᴅᴇᴏ ᴄʜᴀᴛ sᴛᴀʀᴛᴇᴅ 🥳**")


# VC ended notification
@app.on_message(filters.video_chat_ended)
async def vc_ended(_, msg):
    await msg.reply("**😕 ᴠɪᴅᴇᴏ ᴄʜᴀᴛ ᴇɴᴅᴇᴅ 💔**")


# VC members invited notification
@app.on_message(filters.video_chat_members_invited)
async def vc_invited(_, message: Message):
    text = f"➻ {message.from_user.mention}\n\n**๏ ɪɴᴠɪᴛɪɴɢ ɪɴ ᴠᴄ ᴛᴏ :**\n\n**➻ **"
    for user in message.video_chat_members_invited.users:
        try:
            text += f"[{user.first_name}](tg://user?id={user.id}) "
        except Exception:
            pass
    try:
        add_link = f"https://t.me/{app.username}?startgroup=true"
        await message.reply(
            text + " 🤭",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="๏ ᴊᴏɪɴ ᴠᴄ ๏", url=add_link)]]
            ),
        )
    except Exception:
        pass


# /math command — safe eval
@app.on_message(filters.command("math") & ~BANNED_USERS)
async def calculate_math(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("**Usage:** `/math 2+2`")
    expression = message.text.split(None, 1)[1]
    try:
        # Only allow safe characters
        if re.search(r"[a-zA-Z_]", expression):
            raise ValueError("Only numeric expressions allowed")
        result = eval(expression, {"__builtins__": {}})
        await message.reply(f"**ᴛʜᴇ ʀᴇsᴜʟᴛ ɪs :** `{result}`")
    except Exception:
        await message.reply("**❌ ɪɴᴠᴀʟɪᴅ ᴇxᴘʀᴇssɪᴏɴ**")


# /pin — pin a message (admin only)
@app.on_message(filters.command("pin") & filters.group & ~BANNED_USERS)
async def pin_msg(_, message: Message):
    if not message.reply_to_message:
        return await message.reply("**ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴘɪɴ ɪᴛ!**")
    try:
        member = await app.get_chat_member(message.chat.id, message.from_user.id)
        if not member.privileges or not member.privileges.can_pin_messages:
            return await message.reply("**❌ ʏᴏᴜ ɴᴇᴇᴅ ᴘɪɴ ᴍᴇssᴀɢᴇs ᴘᴇʀᴍɪssɪᴏɴ.**")
        await message.reply_to_message.pin()
        await message.reply(
            "**📌 ᴍᴇssᴀɢᴇ ᴘɪɴɴᴇᴅ!**",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📝 ᴠɪᴇᴡ ᴍᴇssᴀɢᴇ", url=message.reply_to_message.link)]]
            ),
        )
    except Exception as e:
        await message.reply(f"**❌ {e}**")


# /unpin — unpin a message (admin only)
@app.on_message(filters.command("unpin") & filters.group & ~BANNED_USERS)
async def unpin_msg(_, message: Message):
    if not message.reply_to_message:
        return await message.reply("**ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴜɴᴘɪɴ ɪᴛ!**")
    try:
        member = await app.get_chat_member(message.chat.id, message.from_user.id)
        if not member.privileges or not member.privileges.can_pin_messages:
            return await message.reply("**❌ ʏᴏᴜ ɴᴇᴇᴅ ᴘɪɴ ᴍᴇssᴀɢᴇs ᴘᴇʀᴍɪssɪᴏɴ.**")
        await message.reply_to_message.unpin()
        await message.reply("**📌 ᴍᴇssᴀɢᴇ ᴜɴᴘɪɴɴᴇᴅ!**")
    except Exception as e:
        await message.reply(f"**❌ {e}**")


# /pinned — show current pinned message
@app.on_message(filters.command("pinned") & filters.group & ~BANNED_USERS)
async def show_pinned(_, message: Message):
    chat = await app.get_chat(message.chat.id)
    if not chat.pinned_message:
        return await message.reply("**ɴᴏ ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ ғᴏᴜɴᴅ.**")
    try:
        await message.reply(
            "**ʜᴇʀᴇ ɪs ᴛʜᴇ ʟᴀᴛᴇsᴛ ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ:**",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📝 ᴠɪᴇᴡ ᴍᴇssᴀɢᴇ", url=chat.pinned_message.link)]]
            ),
        )
    except Exception as e:
        await message.reply(str(e))


# /settitle — change group title (admin only)
@app.on_message(filters.command("settitle") & filters.group & ~BANNED_USERS)
async def set_title(_, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply("**ᴜsᴀɢᴇ: /settitle New Title**")
    try:
        member = await app.get_chat_member(message.chat.id, message.from_user.id)
        if not member.privileges or not member.privileges.can_change_info:
            return await message.reply("**❌ ʏᴏᴜ ɴᴇᴇᴅ ᴄʜᴀɴɢᴇ ɪɴꜰᴏ ᴘᴇʀᴍɪssɪᴏɴ.**")
        title = (message.reply_to_message.text if message.reply_to_message else message.text.split(None, 1)[1])
        await message.chat.set_title(title)
        await message.reply(f"**✅ ɢʀᴏᴜᴘ ᴛɪᴛʟᴇ ᴄʜᴀɴɢᴇᴅ!**\nby {message.from_user.mention}")
    except Exception as e:
        await message.reply(f"**❌ {e}**")


# /setdescription — change group description (admin only)
@app.on_message(filters.command(["setdescription", "setdesc", "setdiscription"]) & filters.group & ~BANNED_USERS)
async def set_desc(_, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply("**ᴜsᴀɢᴇ: /setdescription New description**")
    try:
        member = await app.get_chat_member(message.chat.id, message.from_user.id)
        if not member.privileges or not member.privileges.can_change_info:
            return await message.reply("**❌ ʏᴏᴜ ɴᴇᴇᴅ ᴄʜᴀɴɢᴇ ɪɴꜰᴏ ᴘᴇʀᴍɪssɪᴏɴ.**")
        desc = (message.reply_to_message.text if message.reply_to_message else message.text.split(None, 1)[1])
        await message.chat.set_description(desc)
        await message.reply(f"**✅ ɢʀᴏᴜᴘ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ ᴜᴘᴅᴀᴛᴇᴅ!**\nby {message.from_user.mention}")
    except Exception as e:
        await message.reply(f"**❌ {e}**")


# /setphoto — change group photo (admin only)
@app.on_message(filters.command("setphoto") & filters.group & ~BANNED_USERS)
async def set_photo(_, message: Message):
    if not message.reply_to_message or not (message.reply_to_message.photo or message.reply_to_message.document):
        return await message.reply("**ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴘʜᴏᴛᴏ ᴏʀ ᴅᴏᴄᴜᴍᴇɴᴛ.**")
    try:
        member = await app.get_chat_member(message.chat.id, message.from_user.id)
        if not member.privileges or not member.privileges.can_change_info:
            return await message.reply("**❌ ʏᴏᴜ ɴᴇᴇᴅ ᴄʜᴀɴɢᴇ ɪɴꜰᴏ ᴘᴇʀᴍɪssɪᴏɴ.**")
        photo = await message.reply_to_message.download()
        await message.chat.set_photo(photo=photo)
        await message.reply(f"**✅ ɢʀᴏᴜᴘ ᴘʜᴏᴛᴏ ᴜᴘᴅᴀᴛᴇᴅ!**\nby {message.from_user.mention}")
    except Exception as e:
        await message.reply(f"**❌ {e}**")


# /removephoto — remove group photo (admin only)
@app.on_message(filters.command("removephoto") & filters.group & ~BANNED_USERS)
async def remove_photo(_, message: Message):
    try:
        member = await app.get_chat_member(message.chat.id, message.from_user.id)
        if not member.privileges or not member.privileges.can_change_info:
            return await message.reply("**❌ ʏᴏᴜ ɴᴇᴇᴅ ᴄʜᴀɴɢᴇ ɪɴꜰᴏ ᴘᴇʀᴍɪssɪᴏɴ.**")
        await app.delete_chat_photo(message.chat.id)
        await message.reply(f"**✅ ɢʀᴏᴜᴘ ᴘʜᴏᴛᴏ ʀᴇᴍᴏᴠᴇᴅ!**\nby {message.from_user.mention}")
    except Exception as e:
        await message.reply(f"**❌ {e}**")


# /lg — owner leave chat
@app.on_message(filters.command("lg") & filters.user(OWNER_ID))
async def owner_leave(_, message: Message):
    await message.reply("**sᴜᴄᴄᴇssғᴜʟʟʏ ʜɪʀᴏ !!.**")
    await app.leave_chat(chat_id=message.chat.id, delete=True)


__MODULE__ = "VCᴛᴏᴏʟs"
__HELP__ = """
/math [expr] — ᴄᴀʟᴄᴜʟᴀᴛᴇ ᴍᴀᴛʜ ᴇxᴘʀᴇssɪᴏɴ
/pin — ᴘɪɴ ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ (ᴀᴅᴍɪɴ)
/unpin — ᴜɴᴘɪɴ ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ (ᴀᴅᴍɪɴ)
/pinned — sʜᴏᴡ ᴄᴜʀʀᴇɴᴛ ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ
/settitle [title] — ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ᴛɪᴛʟᴇ (ᴀᴅᴍɪɴ)
/setdescription [desc] — ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ᴅᴇsᴄ (ᴀᴅᴍɪɴ)
/setphoto — ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ᴘʜᴏᴛᴏ, ʀᴇᴘʟʏ ᴛᴏ ɪᴍᴀɢᴇ (ᴀᴅᴍɪɴ)
/removephoto — ʀᴇᴍᴏᴠᴇ ɢʀᴏᴜᴘ ᴘʜᴏᴛᴏ (ᴀᴅᴍɪɴ)
"""
