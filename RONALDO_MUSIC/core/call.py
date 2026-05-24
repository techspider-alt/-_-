import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
)
from pytgcalls.types import (
    Update,
    MediaStream,
    AudioQuality,
    VideoQuality,
    StreamAudioEnded,
    StreamVideoEnded,
)

import config
from RONALDO_MUSIC import LOGGER, YouTube, app
from RONALDO_MUSIC.misc import db
from RONALDO_MUSIC.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from RONALDO_MUSIC.utils.exceptions import AssistantErr
from RONALDO_MUSIC.utils.formatters import check_duration, seconds_to_min, speed_converter
from RONALDO_MUSIC.utils.inline.play import stream_markup, telegram_markup
from RONALDO_MUSIC.utils.logger_card import remove_logger_card, send_logger_card
from RONALDO_MUSIC.utils.stream.autoclear import auto_clean
from RONALDO_MUSIC.utils.thumbnails import get_thumb
from strings import get_string

autoend = {}
counter = {}


async def _clear_(chat_id):
    db[chat_id] = []
    remove_logger_card(chat_id)
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


def _make_call_client(name, session_string):
    return Client(
        name=name,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=session_string,
        no_updates=True,
        in_memory=True,
    )


class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = _make_call_client("DARKXMUSIC1", config.STRING1) if config.STRING1 else None
        self.one = PyTgCalls(self.userbot1, cache_duration=100) if self.userbot1 else None

        self.userbot2 = _make_call_client("DARKXMUSIC2", config.STRING2) if config.STRING2 else None
        self.two = PyTgCalls(self.userbot2, cache_duration=100) if self.userbot2 else None

        self.userbot3 = _make_call_client("DARKXMUSIC3", config.STRING3) if config.STRING3 else None
        self.three = PyTgCalls(self.userbot3, cache_duration=100) if self.userbot3 else None

        self.userbot4 = _make_call_client("DARKXMUSIC4", config.STRING4) if config.STRING4 else None
        self.four = PyTgCalls(self.userbot4, cache_duration=100) if self.userbot4 else None

        self.userbot5 = _make_call_client("DARKXMUSIC5", config.STRING5) if config.STRING5 else None
        self.five = PyTgCalls(self.userbot5, cache_duration=100) if self.userbot5 else None

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def stop_stream_force(self, chat_id: int):
        for c in self._active_clients():
            try:
                await c.leave_group_call(chat_id)
            except:
                pass
        try:
            await _clear_(chat_id)
        except:
            pass

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        if str(speed) != str("1.0"):
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                if str(speed) == str("0.5"):
                    vs = 2.0
                if str(speed) == str("0.75"):
                    vs = 1.35
                if str(speed) == str("1.5"):
                    vs = 0.68
                if str(speed) == str("2.0"):
                    vs = 0.5
                proc = await asyncio.create_subprocess_shell(
                    cmd=(
                        "ffmpeg "
                        "-i "
                        f"{file_path} "
                        "-filter:v "
                        f"setpts={vs}*PTS "
                        "-filter:a "
                        f"atempo={speed} "
                        f"{out}"
                    ),
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            else:
                pass
        else:
            out = file_path
        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        stream = (
            MediaStream(
                out,
                audio_parameters=AudioQuality.HIGH,
                video_parameters=VideoQuality.SD_480p,
                audio_flags=MediaStream.REQUIRED,
                video_flags=MediaStream.REQUIRED,
                ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
            if playing[0]["streamtype"] == "video"
            else MediaStream(
                out,
                audio_parameters=AudioQuality.HIGH,
                audio_flags=MediaStream.REQUIRED,
                video_flags=MediaStream.IGNORE,
                ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
        )
        if str(db[chat_id][0]["file"]) == str(file_path):
            await assistant.change_stream(chat_id, stream)
        else:
            raise AssistantErr("Umm")
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        if video:
            stream = MediaStream(
                link,
                audio_parameters=AudioQuality.HIGH,
                video_parameters=VideoQuality.SD_480p,
                audio_flags=MediaStream.REQUIRED,
                video_flags=MediaStream.REQUIRED,
            )
        else:
            stream = MediaStream(
                link,
                audio_parameters=AudioQuality.HIGH,
                audio_flags=MediaStream.REQUIRED,
                video_flags=MediaStream.IGNORE,
            )
        await assistant.change_stream(
            chat_id,
            stream,
        )

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        stream = (
            MediaStream(
                file_path,
                audio_parameters=AudioQuality.HIGH,
                video_parameters=VideoQuality.SD_480p,
                audio_flags=MediaStream.REQUIRED,
                video_flags=MediaStream.REQUIRED,
                ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
            if mode == "video"
            else MediaStream(
                file_path,
                audio_parameters=AudioQuality.HIGH,
                audio_flags=MediaStream.REQUIRED,
                video_flags=MediaStream.IGNORE,
                ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
        )
        await assistant.change_stream(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOGGER_ID)
        await assistant.join_group_call(
            config.LOGGER_ID,
            MediaStream(link),
        )
        await asyncio.sleep(0.2)
        await assistant.leave_group_call(config.LOGGER_ID)

    def _get_userbot(self, assistant):
        if assistant is self.one:
            return self.userbot1
        elif assistant is self.two:
            return self.userbot2
        elif assistant is self.three:
            return self.userbot3
        elif assistant is self.four:
            return self.userbot4
        elif assistant is self.five:
            return self.userbot5
        return None

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        language = await get_lang(chat_id)
        _ = get_string(language)

        userbot = self._get_userbot(assistant)
        if userbot:
            try:
                await userbot.resolve_peer(chat_id)
            except Exception:
                pass

        if video:
            stream = MediaStream(
                link,
                audio_parameters=AudioQuality.HIGH,
                video_parameters=VideoQuality.SD_480p,
                audio_flags=MediaStream.REQUIRED,
                video_flags=MediaStream.REQUIRED,
            )
        else:
            stream = MediaStream(
                link,
                audio_parameters=AudioQuality.HIGH,
                audio_flags=MediaStream.REQUIRED,
                video_flags=MediaStream.IGNORE,
            )
        try:
            await assistant.join_group_call(
                chat_id,
                stream,
            )
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])
        except Exception as e:
            LOGGER(__name__).error(f"join_group_call failed for {chat_id}: {type(e).__name__}: {e}")
            try:
                await asyncio.sleep(2)
                await assistant.join_group_call(chat_id, stream)
            except NoActiveGroupCall:
                raise AssistantErr(_["call_8"])
            except AlreadyJoinedError:
                raise AssistantErr(_["call_9"])
            except Exception as e2:
                LOGGER(__name__).error(f"join_group_call retry failed for {chat_id}: {type(e2).__name__}: {e2}")
                raise AssistantErr(f"{_['call_10']}\n\n<code>{type(e2).__name__}: {e2}</code>")
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            try:
                users = len(await assistant.get_participants(chat_id))
            except Exception:
                users = 0
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if not check:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)
            if not check:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
        except Exception as e:
            LOGGER(__name__).warning(f"change_stream queue error for {chat_id}: {e}")
            try:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
            except:
                return
        else:
            queued = check[0]["file"]
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0]["title"]).title()
            user = check[0]["by"]
            original_chat_id = check[0]["chat_id"]
            streamtype = check[0]["streamtype"]
            videoid = check[0]["vidid"]
            db[chat_id][0]["played"] = 0
            exis = (check[0]).get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = check[0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0
            video = True if str(streamtype) == "video" else False
            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                if video:
                    stream = MediaStream(
                        link,
                        audio_parameters=AudioQuality.HIGH,
                        video_parameters=VideoQuality.SD_480p,
                        audio_flags=MediaStream.REQUIRED,
                        video_flags=MediaStream.REQUIRED,
                    )
                else:
                    stream = MediaStream(
                        link,
                        audio_parameters=AudioQuality.HIGH,
                        audio_flags=MediaStream.REQUIRED,
                        video_flags=MediaStream.IGNORE,
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                img = await get_thumb(videoid)
                button = telegram_markup(_, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                    has_spoiler=True,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
                await send_logger_card(chat_id, original_chat_id, title, user, "VIDEO" if video else "AUDIO")
            elif "vid_" in queued:
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(
                        videoid,
                        mystic,
                        videoid=True,
                        video=True if str(streamtype) == "video" else False,
                    )
                except:
                    try:
                        file_path, direct = await YouTube.download(
                            videoid,
                            mystic,
                            videoid=True,
                            video=True if str(streamtype) == "video" else False,
                        )
                    except:
                        return await mystic.edit_text(
                            _["call_6"], disable_web_page_preview=True
                        )
                if video:
                    stream = MediaStream(
                        file_path,
                        audio_parameters=AudioQuality.HIGH,
                        video_parameters=VideoQuality.SD_480p,
                        audio_flags=MediaStream.REQUIRED,
                        video_flags=MediaStream.REQUIRED,
                    )
                else:
                    stream = MediaStream(
                        file_path,
                        audio_parameters=AudioQuality.HIGH,
                        audio_flags=MediaStream.REQUIRED,
                        video_flags=MediaStream.IGNORE,
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                img = await get_thumb(videoid)
                button = stream_markup(_, videoid, chat_id)
                await mystic.delete()
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                    has_spoiler=True,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
                await send_logger_card(chat_id, original_chat_id, title, user, "VIDEO" if video else "AUDIO")
            elif "index_" in queued:
                stream = (
                    MediaStream(
                        videoid,
                        audio_parameters=AudioQuality.HIGH,
                        video_parameters=VideoQuality.SD_480p,
                        audio_flags=MediaStream.REQUIRED,
                        video_flags=MediaStream.REQUIRED,
                    )
                    if str(streamtype) == "video"
                    else MediaStream(
                        videoid,
                        audio_parameters=AudioQuality.HIGH,
                        audio_flags=MediaStream.REQUIRED,
                        video_flags=MediaStream.IGNORE,
                    )
                )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                button = telegram_markup(_, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=config.STREAM_IMG_URL,
                    caption=_["stream_2"].format(user),
                    reply_markup=InlineKeyboardMarkup(button),
                    has_spoiler=True,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
                await send_logger_card(chat_id, original_chat_id, title, user, "VIDEO" if video else "AUDIO")
            else:
                if video:
                    stream = MediaStream(
                        queued,
                        audio_parameters=AudioQuality.HIGH,
                        video_parameters=VideoQuality.SD_480p,
                        audio_flags=MediaStream.REQUIRED,
                        video_flags=MediaStream.REQUIRED,
                    )
                else:
                    stream = MediaStream(
                        queued,
                        audio_parameters=AudioQuality.HIGH,
                        audio_flags=MediaStream.REQUIRED,
                        video_flags=MediaStream.IGNORE,
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                if videoid == "telegram":
                    button = telegram_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=(
                            config.TELEGRAM_AUDIO_URL
                            if str(streamtype) == "audio"
                            else config.TELEGRAM_VIDEO_URL
                        ),
                        caption=_["stream_1"].format(
                            config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                        has_spoiler=True,
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                    await send_logger_card(chat_id, original_chat_id, title, user, "VIDEO" if video else "AUDIO")
                elif videoid == "soundcloud":
                    button = telegram_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=config.SOUNCLOUD_IMG_URL,
                        caption=_["stream_1"].format(
                            config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                        has_spoiler=True,
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                    await send_logger_card(chat_id, original_chat_id, title, user, "AUDIO")
                else:
                    img = await get_thumb(videoid)
                    button = stream_markup(_, videoid, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{videoid}",
                            title[:23],
                            check[0]["dur"],
                            user,
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                        has_spoiler=True,
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"
                    await send_logger_card(chat_id, original_chat_id, title, user, "VIDEO" if video else "AUDIO")

    async def ping(self):
        pings = []
        for c in self._active_clients():
            try:
                pings.append(await c.ping)
            except:
                pass
        if not pings:
            return "0"
        return str(round(sum(pings) / len(pings), 3))

    def _active_clients(self):
        return [c for c in [self.one, self.two, self.three, self.four, self.five] if c is not None]

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        for client in self._active_clients():
            try:
                await client.start()
            except Exception as e:
                LOGGER(__name__).warning(f"PyTgCalls start skipped (already running?): {e}")

    async def decorators(self):
        active = self._active_clients()
        if not active:
            return

        async def stream_services_handler(_, chat_id: int):
            await self.stop_stream(chat_id)

        async def stream_end_handler1(client, update: Update):
            if not isinstance(update, (StreamAudioEnded, StreamVideoEnded)):
                return
            await self.change_stream(client, update.chat_id)

        for c in active:
            c.on_kicked()(stream_services_handler)
            c.on_closed_voice_chat()(stream_services_handler)
            c.on_left()(stream_services_handler)
            c.on_stream_end()(stream_end_handler1)


RONALDO = Call()
