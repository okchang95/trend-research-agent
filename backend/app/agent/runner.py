import logging
from typing import AsyncIterator

from app.agent.graph import graph_builder
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


class AgentRunner:
    def __init__(self):
        self.graph_app = graph_builder().compile()

    async def run(self, user_message: str):
        """동기 실행 (기존 호환성 유지)"""
        state = AgentState(user_message=user_message)
        try:
            result_state = await self.graph_app.ainvoke(state)
            return {"result_state": result_state}
        except Exception as e:
            logger.error(f"Error: {e}")
            raise RuntimeError("Agent request failed.")

    async def stream(self, user_message: str) -> AsyncIterator[dict]:
        """SSE를 위한 스트리밍 실행"""
        initial_state = AgentState(user_message=user_message)
        final_state = None
        
        try:
            async for event in self.graph_app.astream(initial_state):
                # 각 노드의 실행 결과를 스트리밍
                # event는 {node_name: state} 형태의 딕셔너리
                for node_name, node_state in event.items():
                    final_state = node_state  # 마지막 상태 저장
                    yield {
                        "type": "node_complete",
                        "node": node_name,
                        "state": dict(node_state),  # TypedDict를 dict로 변환
                    }
            
            # 최종 상태 전송
            if final_state:
                yield {
                    "type": "final",
                    "state": dict(final_state),
                }
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "type": "error",
                "error": str(e),
            }
