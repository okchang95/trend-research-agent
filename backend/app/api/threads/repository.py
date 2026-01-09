from pymongo.database import Database

from app.db.collectios import MongoCollections


class ThreadRepository:
    def __init__(self, db: Database):
        self._col = db[MongoCollections.THREADS]

    async def create(self, data: dict):
        result = await self._col.insert_one(data)
        return result.inserted_id

    async def get_all(self):
        threads = await self._col.find().to_list(length=None)
        return threads
