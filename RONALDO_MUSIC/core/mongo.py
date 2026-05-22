from motor.motor_asyncio import AsyncIOMotorClient as _mongo_client_
from pymongo import MongoClient

import config

from ..logging import LOGGER

if config.MONGO_DB_URI is None:
    LOGGER(__name__).error(
        "MONGO_DB_URI is not set! Please add your MongoDB connection string to environment variables."
    )
    raise SystemExit("MONGO_DB_URI is required. Get it from cloud.mongodb.com")

_mongo_async_ = _mongo_client_(config.MONGO_DB_URI)
_mongo_sync_ = MongoClient(config.MONGO_DB_URI)
mongodb = _mongo_async_.RONALDO_MUSIC
pymongodb = _mongo_sync_.RONALDO_MUSIC
