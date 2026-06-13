import asyncio

from RONALDO_MUSIC.misc import db, advancing_chats
from RONALDO_MUSIC.utils.database import get_active_chats, is_music_playing


async def _seeker_advance(chat_id: int):
    """
    Fallback queue advancement triggered when the seeker timer expires.
    Waits 4 seconds so the StreamAudioEnded handler (which has a 1s delay)
    always runs first when it fires. If change_stream() was already called by
    the StreamAudioEnded path, it will have discarded chat_id from
    advancing_chats, and we bail out cleanly without double-advancing.
    """
    await asyncio.sleep(4)
    if chat_id not in advancing_chats:
        return  # StreamAudioEnded already handled it — nothing to do
    advancing_chats.discard(chat_id)
    try:
        from RONALDO_MUSIC import LOGGER
        from RONALDO_MUSIC.core.call import RONALDO
        from RONALDO_MUSIC.utils.database import group_assistant
        LOGGER(__name__).info(
            f"[seeker] StreamAudioEnded missed for {chat_id} — running fallback"
        )
        client = await group_assistant(RONALDO, chat_id)
        if client:
            await RONALDO.change_stream(client, chat_id)
    except Exception as _e:
        try:
            from RONALDO_MUSIC import LOGGER
            LOGGER(__name__).warning(f"[seeker] fallback error for {chat_id}: {_e}")
        except Exception:
            pass


async def timer():
    while not await asyncio.sleep(1):
        try:
            active_chats = await get_active_chats()
        except Exception:
            continue
        for chat_id in active_chats:
            try:
                if not await is_music_playing(chat_id):
                    continue
                playing = db.get(chat_id)
                if not playing:
                    continue
                duration = int(playing[0].get("seconds", 0))
                if duration == 0:
                    continue
                played = int(db[chat_id][0].get("played", 0))
                if played >= duration:
                    # Timer expired — schedule seeker fallback once per song-end event
                    if chat_id not in advancing_chats:
                        advancing_chats.add(chat_id)
                        asyncio.create_task(_seeker_advance(chat_id))
                    continue
                db[chat_id][0]["played"] = played + 1
            except Exception:
                continue


asyncio.create_task(timer())
