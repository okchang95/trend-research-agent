from fastapi import Depends
from pymongo.database import Database

from app.api.chat.repository import (
    ChatMessageRepository,
    ChatThreadRepository,
)
from app.api.chat.service import (
    ChatService,
    ChatThreadService,
    ChatMessageService,
)
from app.db.deps import get_mongo_db


############################################################
#
# Threads Dependencies
#
############################################################
def get_chat_thread_repo(db: Database = Depends(get_mongo_db)) -> ChatThreadRepository:
    return ChatThreadRepository(db)


def get_chat_thread_service(
    repo: ChatThreadRepository = Depends(get_chat_thread_repo),
) -> ChatThreadService:
    return ChatThreadService(repo)


############################################################
#
# Messages Dependencies
#
############################################################
def get_chat_message_repo(
    db: Database = Depends(get_mongo_db),
) -> ChatMessageRepository:
    return ChatMessageRepository(db)


def get_chat_message_service(
    repo: ChatMessageRepository = Depends(get_chat_message_repo),
) -> ChatMessageService:
    return ChatMessageService(repo)


############################################################
#
# Agent Dependencies
#
############################################################
def get_chat_service(
    repo_chat_message: ChatMessageRepository = Depends(get_chat_message_repo),
    repo_chat_thread: ChatThreadRepository = Depends(get_chat_thread_repo),
) -> ChatService:
    return ChatService(
        _repo_chat_message=repo_chat_message,
        _repo_chat_thread=repo_chat_thread,
    )
