"""
MongoDB 컬렉션 이름 정의
- 모든 데이터베이스 컬렉션명을 Enum으로 중앙 관리
"""

from enum import Enum


class MongoCollections(str, Enum):
    USERS = "users"
    CHAT_THREADS = "chat_threads"
    CHAT_MESSAGES = "chat_messages"
