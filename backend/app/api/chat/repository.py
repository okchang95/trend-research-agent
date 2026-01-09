from bson import ObjectId
from datetime import datetime
from pymongo.database import Database

from app.db.collections import MongoCollections


class ChatThreadRepository:
    def __init__(self, db: Database):
        self._col = db[MongoCollections.CHAT_THREADS]

    # CREATE
    async def create(self, data: dict):
        result = await self._col.insert_one(data)
        return result.inserted_id

    # READ ALL
    async def get_all(self):
        return await self._col.find().to_list(length=None)

    # READ BY USER_ID
    async def get_by_user_id(self, user_id: str):
        filter_ = {"user_id": ObjectId(user_id)}
        return await self._col.find_one(filter=filter_)

    # READ BY ObjectId
    async def get_by_oid(self, oid: str):
        filter_ = {"_id": ObjectId(oid)}
        return await self._col.find_one(filter=filter_)

    # UPDATE
    async def update(self, oid: str, update_set: dict):
        filter_ = {"_id": ObjectId(oid)}
        update_ = {"$set": update_set}
        return await self._col.update_one(filter=filter_, update=update_)

    # DELETE
    async def delete(self, oid: str):
        filter_ = {"_id": ObjectId(oid)}
        result = await self._col.delete_one(filter=filter_)
        return result.deleted_count


class ChatMessageRepository:
    def __init__(self, db: Database):
        self._col = db[MongoCollections.CHAT_MESSAGES]

    # CREATE
    async def create(self, data: dict):
        return await self._col.insert_one(data)

    # READ ALL BY THREAD_ID
    async def get_by_thread_id(self, thread_id: str):
        filter_ = {"thread_id": ObjectId(thread_id)}
        return await self._col.find(filter=filter_).to_list(length=None)

    # READ UNSUMMARIZED MESSAGES
    async def get_unsummarized_by_thread_id(
        self,
        thread_id: str,
        last_summarized_at: datetime | None,
    ):
        filter_ = {"thread_id": ObjectId(thread_id)}
        if last_summarized_at:
            filter_["timestamp"] = {"$gt": last_summarized_at}

        return (
            await self._col.find(filter=filter_)
            .sort("timestamp", 1)
            .to_list(length=None)
        )
