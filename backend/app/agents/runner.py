import asyncio
import logging
import uuid
from typing import AsyncIterator, List, Dict

from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import graph_builder
from app.agents.state import AgentState
from app.agents.streaming.event_handlers import StreamEventHandler

logger = logging.getLogger(__name__)


class AgentRunner:
    def __init__(self):
        # 메모리 체크포인터 추가 (astream_events 사용을 위해)
        memory = MemorySaver()
        self.graph_app = graph_builder().compile(checkpointer=memory)

    async def stream(
        self,
        user_message: str,
        conversations: List[Dict],
        conversations_summary: str,
        cancel_event: "asyncio.Event" = None,
    ) -> AsyncIterator[Dict]:
        """
        SSE를 위한 스트리밍 실행
        astream_events를 사용하여 노드 시작/완료, LLM 스트리밍, 도구 실행 이벤트 감지

        Args:
            user_message: 사용자 메시지
            conversations: 대화 기록
            conversations_summary: 대화 요약
            cancel_event: 취소 이벤트 (중지 버튼용)
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

            # astream_events를 사용하여 노드 시작/완료, LLM 스트리밍, 도구 실행 이벤트 감지
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
                # 취소 체크 (중지 버튼)
                if cancel_event and cancel_event.is_set():
                    logger.info("Agent stream cancelled by user")
                    break

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
