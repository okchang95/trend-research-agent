from datetime import datetime
from typing import Dict, List, Literal, TypedDict, Optional

# session_id -> Session 매핑
"""
{
    uuid: {
        "conversations_summary": str, 
        "conversations": [
            {
                "role": ...,
                "message": ...,
                "timestamp": ...,
            },
            ...
        ],
    }
}
"""
SESSION_STORE: Dict[str, Dict] = {}
TTL = 60 * 60 * 24  # 24시간 (필요시 사용)


# 채팅 메시지 타입 정의 (타입 힌팅용)
class ChatMessage(TypedDict):
    role: Literal["user", "assistant"]
    message: str
    timestamp: datetime


class Session(TypedDict):
    conversations_summary: str
    conversations: List[ChatMessage]


class SessionManager:
    @staticmethod
    def get_all_sessions() -> Dict[str, Dict]:
        """모든 세션 가져오기

        Returns:
            List[Dict]: 모든 세션 데이터
        """
        return SESSION_STORE

    @staticmethod
    def get_or_create_session(session_id: str) -> Dict:
        """세션 가져오기 또는 생성

        Args:
            session_id: 세션 ID

        Returns:
            Dict: 세션 데이터

        Raises:
            None
        """
        if session_id not in SESSION_STORE:
            SESSION_STORE[session_id] = {
                "conversations_summary": "",
                "conversations": [],
            }
        return SESSION_STORE[session_id]

    @staticmethod
    def set_conversations_summary(session_id: str, summary: str):
        """세션의 conversations_summary 설정

        Args:
            session_id: 세션 ID
            summary: 컨텍스트 요약

        Returns:
            None
        """
        session = SessionManager.get_or_create_session(session_id)
        session["conversations_summary"] = summary

    @staticmethod
    def add_message(session_id: str, role: Literal["user", "assistant"], message: str):
        """세션에 메시지 추가

        Args:
            session_id: 세션 ID
            role: 메시지 역할
            message: 메시지

        Returns:
            None
        """
        session = SessionManager.get_or_create_session(session_id)
        session["conversations"].append(
            {"role": role, "message": message, "timestamp": datetime.now()}
        )

    @staticmethod
    def update_messages(session_id: str, messages: dict):
        """세션의 메시지 업데이트

        Args:
            session_id: 세션 ID
            messages: 메시지 리스트

        Returns:
            None
        """
        session = SessionManager.get_or_create_session(session_id)
        session["conversations"] = messages

    @staticmethod
    def delete_session(session_id: str):
        """세션 삭제

        Args:
            session_id: 세션 ID

        Returns:
            None
        """
        if session_id in SESSION_STORE:
            del SESSION_STORE[session_id]
