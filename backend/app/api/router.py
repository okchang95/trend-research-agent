from fastapi import APIRouter, Depends

from app.api.service import ChatService
from app.api.schemas import ChatRequest, ChatResponse
from app.api.sse import create_sse_response

router = APIRouter()


def get_chat_service() -> ChatService:
    return ChatService()


@router.post("/chat")
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    response = await service.conversation(request.session_id, request.user_message)
    return ChatResponse(**response)


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


@router.get("/sessions")
async def get_all_sessions(service: ChatService = Depends(get_chat_service)):
    sessions = await service.get_all_sessions()
    return sessions
