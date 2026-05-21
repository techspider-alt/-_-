from motor.motor_asyncio import AsyncIOMotorClient as _mongo_client_
from pymongo import MongoClient
from pyrogram import Client

import config

from ..logging import LOGGER

TEMP_MONGODB = "mongodb+srv://darklordsaura:H7wUo2r3i49sOeoe@cluster0.xad2czd.mongodb.net/?appName=Cluster0"


if config.MONGO_DB_URI is None:
    LOGGER(__name__).warning(
        "𝐍o 𝐌ONGO 𝐃B 𝐔RL 𝐅ound.. 𝐘our 𝐁ot 𝐖ill 𝐖ork 𝐎n NOBITA_MUSIC 𝐃atabase"
    )
    temp_client = Client(
        "NOBITA_MUSIC",
        bot_token=config.BOT_TOKEN,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
    )
    temp_client.start()
    info = temp_client.get_me()
    username = info.username
    temp_client.stop()
    _mongo_async_ = _mongo_client_(TEMP_MONGODB)
    _mongo_sync_ = MongoClient(TEMP_MONGODB)
    mongodb = _mongo_async_[username]
    pymongodb = _mongo_sync_[username]
else:
    _mongo_async_ = _mongo_client_(config.MONGO_DB_URI)
    _mongo_sync_ = MongoClient(config.MONGO_DB_URI)
    mongodb = _mongo_async_.Yukki
    pymongodb = _mongo_sync_.Yukki
