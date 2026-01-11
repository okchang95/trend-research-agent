from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field


class User(BaseModel):
    """
    User model
    - 간단하게 이름, 비밀번호로 유저가 등록
    - demo 환경이라 비밀번호 보안 로직은 제외 (TODO: 비밀번호 보안 로직 추가)
    """

    name: str
    password: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=ZoneInfo("Asia/Seoul"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=ZoneInfo("Asia/Seoul"))
    )
