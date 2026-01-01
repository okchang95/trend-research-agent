from fastapi import APIRouter, Depends

from app.api.service import AgentService
from app.api.schemas import AgentRequest, AgentResponse

router = APIRouter()


def get_agent_service() -> AgentService:
    return AgentService()


@router.post("/agent")
async def run_agent(
    request: AgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    response = await service.run_agent(request)
    return AgentResponse(agent_response=response.agent_response)
