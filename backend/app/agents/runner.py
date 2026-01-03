import logging
import uuid
from typing import AsyncIterator, List, Dict

from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import graph_builder
from app.agents.state import AgentState
from app.agents.event_handlers import StreamEventHandler

logger = logging.getLogger(__name__)


class AgentRunner:
    def __init__(self):
        # 메모리 체크포인터 추가 (astream_events 사용을 위해)
        memory = MemorySaver()
        self.graph_app = graph_builder().compile(checkpointer=memory)

    async def run(
        self, user_message: str, conversations: List[Dict], conversations_summary: str
    ):
        # AgentState의 모든 필수 필드 초기화
        state = AgentState(
            current_node="",
            user_message=user_message,
            conversations=conversations,
            conversations_summary=conversations_summary,
            is_clarified=False,
            reason="",
            subject="",
            scope="",
            brief_requirement="",
            findings=[],
            answer="",
        )
        try:
            result_state = await self.graph_app.ainvoke(state)
            logger.info(f"Result state: {result_state}")
            return {
                "answer": result_state.get("answer", ""),
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            raise RuntimeError("Agent request failed.")

    async def stream(
        self, user_message: str, conversations: List[Dict], conversations_summary: str
    ) -> AsyncIterator[Dict]:
        """
        SSE를 위한 스트리밍 실행
        astream_events를 사용하여 노드 시작/완료 이벤트를 정확히 감지
        """
        # AgentState의 모든 필수 필드 초기화
        initial_state = AgentState(
            current_node="",
            user_message=user_message,
            conversations=conversations,
            conversations_summary=conversations_summary,
            is_clarified=False,
            reason="",
            subject="",
            scope="",
            brief_requirement="",
            findings=[],
            answer="",
        )

        # 이벤트 핸들러 초기화
        event_handler = StreamEventHandler()
        event_handler.reset()

        try:
            # 체크포인트용 thread_id 생성
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}

            # astream_events를 사용하여 노드 시작/완료 이벤트 감지
            # LLM 스트리밍을 포함한 모든 이벤트 감지
            async for event in self.graph_app.astream_events(
                initial_state,
                version="v2",
                config=config,
                include_events=[
                    "on_chain_start",
                    "on_chain_end",
                    "on_chat_model_stream",
                    "on_chat_model_end",
                    "on_tool_start",
                    "on_tool_end",
                ],
            ):
                event_type = event.get("event", "")

                # 이벤트 타입별 핸들러 호출
                if event_type == "on_tool_start":
                    async for e in event_handler.handle_tool_start(event):
                        yield e
                elif event_type == "on_tool_end":
                    async for e in event_handler.handle_tool_end(event):
                        yield e
                elif event_type == "on_chat_model_end":
                    await event_handler.handle_chat_model_end(event)
                elif event_type == "on_chat_model_stream":
                    async for e in event_handler.handle_chat_model_stream(event):
                        yield e
                elif event_type == "on_chain_start":
                    async for e in event_handler.handle_chain_start(event):
                        yield e
                elif event_type == "on_chain_end":
                    async for e in event_handler.handle_chain_end(event):
                        yield e

            # 최종 상태 전송
            async for e in event_handler.handle_final_state():
                yield e

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            import traceback

            traceback.print_exc()
            yield {
                "type": "error",
                "error": str(e),
            }


#     async def stream(self, user_message: str) -> AsyncIterator[dict]:
#         """SSE를 위한 스트리밍 실행"""
#         initial_state = AgentState(
#             user_message=user_message,
#             context=[],
#             conversations_summary="",
#             answer="",
#         )
#         final_state = None

#         try:
#             async for event in self.graph_app.astream(initial_state):
#                 # 각 노드의 실행 결과를 스트리밍
#                 # event는 {node_name: state} 형태의 딕셔너리
#                 for node_name, node_state in event.items():
#                     final_state = node_state  # 마지막 상태 저장
#                     yield {
#                         "type": "node_complete",
#                         "node": node_name,
#                         "state": dict(node_state),  # TypedDict를 dict로 변환
#                     }

#             # 최종 상태 전송
#             if final_state:
#                 yield {
#                     "type": "final",
#                     "state": dict(final_state),
#                 }

#         except Exception as e:
#             logger.error(f"Streaming error: {e}")
#             yield {
#                 "type": "error",
#                 "error": str(e),
#             }


# if __name__ == "__main__":
#     import asyncio

#     user_message = ""
#     runner = AgentRunner()
#     asyncio.run(runner.run("Hello, how are you?"))
