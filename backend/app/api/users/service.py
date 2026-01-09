from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from app.api.users.models import User
from app.api.users.repository import UserRepository
from app.api.users.schemas import *


class UserService:
    def __init__(self, repo: UserRepository):
        self._repo = repo

    async def create_user(self, payload: UserCreate):
        name = payload.name
        password = payload.password

        KST = ZoneInfo("Asia/Seoul")
        now_kst = datetime.now(tz=KST)

        # 이미 존재하는 유저인지 확인
        existing_user = await self._repo.get_by_name(name)
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 존재하는 유저입니다.")

        # 유저 데이터 생성
        user_data = User(
            name=name,
            password=password,
            created_at=now_kst,
            updated_at=now_kst,
        ).model_dump()

        new_user_id = await self._repo.create(user_data)
        return {
            "id": str(new_user_id),
            "name": name,
            "created_at": now_kst,
            "updated_at": now_kst,
        }

    async def get_user_by_name(self, name: str):
        user_data = await self._repo.get_by_name(name)
        if not user_data:
            raise HTTPException(status_code=404, detail="존재하지 않는 유저입니다.")
        return {
            "id": str(user_data["_id"]),
            "name": user_data["name"],
            "password": user_data["password"],
            "created_at": user_data["created_at"],
            "updated_at": user_data["updated_at"],
        }
