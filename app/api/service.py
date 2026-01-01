import logging
from typing import AsyncIterator

from fastapi.responses import StreamingResponse
import json

from app.agent.runner import AgentRunner
from app.api.schemas import AgentRequest

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self):
        self.agent_runner = AgentRunner()

    async def run_agent(self, request: AgentRequest):
        """동기 실행 (기존 호환성 유지)"""
        user_message = request.user_message
        try:
            result = await self.agent_runner.run(user_message)
            logger.info(f"Agent response: {result}")
        except Exception as e:
            logger.error(f"Error: {e}")
            raise RuntimeError("Agent request failed.") from e

        return result

    async def stream_agent(self, request: AgentRequest) -> AsyncIterator[str]:
        """SSE를 위한 스트리밍 실행"""
        user_message = request.user_message
        
        try:
            async for event in self.agent_runner.stream(user_message):
                # SSE 형식으로 데이터 전송
                data = json.dumps(event, ensure_ascii=False, default=str)
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_data = json.dumps({
                "type": "error",
                "error": str(e)
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
