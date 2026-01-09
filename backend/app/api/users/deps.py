from fastapi import Depends
from pymongo.database import Database

from app.db.deps import get_mongo_db
from app.api.users.repository import UserRepository
from app.api.users.service import UserService


def get_user_repo(db: Database = Depends(get_mongo_db)) -> UserRepository:
    """
    repository에 db 주입
    """
    return UserRepository(db)


def get_user_service(repo: UserRepository = Depends(get_user_repo)) -> UserService:
    """
    service에 repository 주입
    """
    return UserService(repo)
