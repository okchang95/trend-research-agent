from enum import Enum
from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.db.types import PyObjectId


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """
    chat_messages collection model (Message)
    """

    thread_id: PyObjectId
    role: MessageRole
    ended_node: Optional[str] = Field(default=None)
    message: Optional[str] = Field(default=None)
    report_summary: Optional[str] = Field(default=None)
    findings: Optional[List[dict]] = Field(default=None)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=ZoneInfo("Asia/Seoul"))
    )


class ChatThread(BaseModel):
    """
    chat_threads collection model (Thread)
    - 채팅방 + short term memory
    """

    user_id: PyObjectId
    title: str = Field(default="New Thread")
    conversation_summary: str = Field(default="")
    last_summarized_at: datetime = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=ZoneInfo("Asia/Seoul"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=ZoneInfo("Asia/Seoul"))
    )
