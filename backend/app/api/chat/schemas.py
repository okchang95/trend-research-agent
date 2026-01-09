from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None)
    user_message: str


class ChatResponse(BaseModel):
    session_id: str
    assistant_message: Optional[str] = Field(default=None)
