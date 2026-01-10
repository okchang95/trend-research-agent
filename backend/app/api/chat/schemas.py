from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.chat.models import MessageRole, ThreadStatus


############################################################
#
# Chat Thread Schemas
#
############################################################
class ChatThreadCreate(BaseModel):
    user_id: str


class ChatThreadResponse(BaseModel):
    thread_id: str
    title: str
    status: ThreadStatus
    created_at: datetime
    updated_at: datetime


############################################################
#
# Chat Message Schemas
#
############################################################
class ChatMessageResponse(BaseModel):
    message_id: str
    thread_id: str
    role: MessageRole
    message: str
    findings: Optional[List[dict]] = None
    timestamp: datetime


############################################################
#
# Chat Request Schemas
#
############################################################
class ChatRequest(BaseModel):
    user_id: str
    thread_id: Optional[str] = Field(default=None)
    user_message: str


class ChatResponse(BaseModel):
    thread_id: str
    assistant_message: Optional[str] = Field(default=None)


class CancelRequest(BaseModel):
    thread_id: str
    user_id: str
    partial_message: str = Field(default="")
