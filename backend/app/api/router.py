from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.service import AgentService
from app.api.schemas import AgentRequest

router = APIRouter()


def get_agent_service() -> AgentService:
    return AgentService()


@router.post("/agent")
async def run_agent(
    request: AgentRequest,
    service: AgentService = Depends(get_agent_service),
):
    """동기 실행 (기존 호환성 유지)"""
    response = await service.run_agent(request)
    return response


@router.post("/agent/stream")
async def stream_agent(
    request: AgentRequest,
    service: AgentService = Depends(get_agent_service),
):
    """SSE를 통한 스트리밍 실행"""
    return StreamingResponse(
        service.stream_agent(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
