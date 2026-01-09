from datetime import datetime
from zoneinfo import ZoneInfo

from bson import ObjectId
from pymongo.database import Database

from app.db.collectios import MongoCollections


class UserRepository:
    def __init__(self, db: Database):
        self._col = db[MongoCollections.USERS]

    async def create(self, data: dict):
        result = await self._col.insert_one(data)
        return result.inserted_id

    async def get_by_name(self, name: str):
        user = await self._col.find_one({"name": name})
        return user

    async def get_by_id(self, user_id: str):
        user = await self._col.find_one({"_id": ObjectId(user_id)})
        return user
