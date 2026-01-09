from fastapi import APIRouter, Depends

from app.api.chat.service import ChatService
from app.api.chat.schemas import ChatRequest
from app.api.chat.sse import create_sse_response

router = APIRouter()


def get_chat_service() -> ChatService:
    return ChatService()


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    """
    SSE를 통한 스트리밍 채팅
    각 노드의 실행 결과와 최종 텍스트를 실시간으로 전송
    """
    event_generator = service.stream_conversation(
        request.session_id, request.user_message
    )
    return create_sse_response(event_generator)
