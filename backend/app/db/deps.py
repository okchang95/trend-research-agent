from fastapi import Request
from pymongo.database import Database


def get_mongo_db(request: Request) -> Database:
    """
    request.app.state.mongo_db 에서 mongo db를 가져오는 함수
    """
    db = getattr(request.app.state, "mongo_db", None)
    if db is None:
        raise RuntimeError(
            "MongoDB is not initialized (app.state.mongo_db is missing)."
        )
    return db
