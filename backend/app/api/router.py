from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json

from app.api.service import ChatService
from app.api.schemas import ChatRequest, ChatResponse

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
    async def event_generator():
        try:
            async for event in service.stream_conversation(
                request.session_id, request.user_message
            ):
                # SSE 형식으로 데이터 전송
                data = json.dumps(event, ensure_ascii=False, default=str)
                yield f"data: {data}\n\n"
        except Exception as e:
            error_data = json.dumps(
                {"type": "error", "error": str(e)}, ensure_ascii=False
            )
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions")
async def get_all_sessions(service: ChatService = Depends(get_chat_service)):
    sessions = await service.get_all_sessions()
    return sessions
