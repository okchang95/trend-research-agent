from fastapi import Depends
from pymongo.database import Database

from app.db.deps import get_mongo_db
from app.api.threads.repository import ThreadRepository
from app.api.threads.service import ThreadService


def get_thread_repo(db: Database = Depends(get_mongo_db)) -> ThreadRepository:
    """
    repository에 db 주입
    """
    return ThreadRepository(db)


def get_thread_service(
    repo: ThreadRepository = Depends(get_thread_repo),
) -> ThreadService:
    """
    service에 repository 주입
    """
    return ThreadService(repo)
