from pydantic import BaseModel
from datetime import datetime


class Thread(BaseModel):
    """
    Thread model
    : 채팅방
    """

    title: str
    created_at: datetime
    updated_at: datetime
