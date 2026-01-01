import logging

from app.agent.runner import AgentRunner
from app.api.schemas import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self):
        self.agent_runner = AgentRunner()

    async def run_agent(self, request: AgentRequest) -> AgentResponse:
        user_message = request.user_message
        try:
            result = await self.agent_runner.run(user_message)
            logger.info(f"Agent response: {result}")
        except Exception as e:
            logger.error(f"Error: {e}")
            raise RuntimeError("Agent request failed.") from e

        return AgentResponse(agent_response="test")
