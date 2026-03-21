from pymongo import MongoClient

from config import Config


_client = None
_db = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            Config.MONGODB_URI,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=2000,
        )
    return _client


def get_db():
    global _db
    if _db is None:
        _db = get_client()[Config.DB_NAME]
    return _db


def get_collection(name: str):
    return get_db()[name]
