import logging
import json
import uuid
from typing import AsyncIterator, Dict

from app.agents.runner import AgentRunner
from app.api.session import SessionManager
from app.utils import date_to_str_recursive

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.agent_runner = AgentRunner()

    async def conversation(self, session_id: str, user_message: str):

        # session_id가 없으면 새로운 세션 생성
        if not session_id:
            logger.info(f"No session_id provided. Creating new session.")
            session_id = str(uuid.uuid4())
            logger.info(f"New session_id: {session_id}")

        session = SessionManager.get_or_create_session(session_id)
        conversations_summary = session.get("conversations_summary", "")

        # 메시지 추가
        SessionManager.add_message(session_id, "user", user_message)

        # 에이전트 실행
        try:
            response = await self.agent_runner.run(
                user_message=user_message,
                conversations=session.get("conversations", []),
                conversations_summary=conversations_summary,
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            response = {"answer": "응답 실패"}

        # 메시지 추가
        assistant_message = response.get("answer", "")
        SessionManager.add_message(session_id, "assistant", assistant_message)

        # 컨텍스트 요약 업데이트 (10턴 = 20개 메시지에서 최근 6턴 = 12개 메시지를 남기고 나머지 요약)
        conversations = session.get("conversations", [])
        if len(conversations) >= 20:  # 10턴 = 20개 메시지
            # 최근 6턴(12개 메시지)은 유지, 나머지 4턴(8개 메시지)은 요약
            old_conversations = conversations[:-12]  # 요약할 대화 (4턴 = 8개 메시지)
            recent_conversations = conversations[-12:]  # 유지할 대화 (6턴 = 12개 메시지)

            new_summized_conversations = await self._summarize_context(
                old_conversations, conversations_summary
            )
            SessionManager.set_conversations_summary(
                session_id, new_summized_conversations
            )
            SessionManager.update_messages(session_id, recent_conversations)

        return {
            "assistant_message": assistant_message,
            "session_id": session_id,
        }

    async def _summarize_context(self, conversations, conversations_summary):
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import PromptTemplate
        from app.core.config import Config

        config = Config()
        llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY
        )
        template = """
        You are a helpful assistant that summarizes conversations.
        You are given a conversation and a context summary before conversations.
        You need to summarize the conversation and update the context summary.

        Context summary: {conversations_summary}
        Conversation: {conversation}

        Return the updated context summary only.
        Updated context summary:
        """
        prompt = PromptTemplate(
            template=template.replace("  ", "").strip(),
            input_variables=["conversations_summary", "conversation"],
        )
        chain = prompt | llm
        result = await chain.ainvoke(
            {
                "conversations_summary": conversations_summary,
                "conversation": conversations,
            }
        )
        return result.content

    async def get_all_sessions(self):
        return SessionManager.get_all_sessions()

    async def stream_conversation(
        self, session_id: str, user_message: str
    ) -> AsyncIterator[Dict]:
        """
        SSE를 위한 스트리밍 대화
        각 노드의 실행 결과와 최종 텍스트를 스트리밍으로 전송
        """
        import uuid

        # session_id가 없으면 새로운 세션 생성
        if not session_id:
            logger.info(f"No session_id provided. Creating new session.")
            session_id = str(uuid.uuid4())
            logger.info(f"New session_id: {session_id}")

        session = SessionManager.get_or_create_session(session_id)
        conversations_summary = session.get("conversations_summary", "")

        # 메시지 추가
        SessionManager.add_message(session_id, "user", user_message)

        # 세션 ID 전송
        yield {
            "type": "session",
            "session_id": session_id,
        }

        final_answer = None

        try:
            # 에이전트 스트리밍 실행
            async for event in self.agent_runner.stream(
                user_message=user_message,
                conversations=session.get("conversations", []),
                conversations_summary=conversations_summary,
            ):
                # final 이벤트에서 answer 추출
                if event.get("type") == "final":
                    final_answer = event.get("state", {}).get("answer", "")

                yield event

            # 최종 메시지 저장
            if final_answer:
                SessionManager.add_message(session_id, "assistant", final_answer)

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "type": "error",
                "error": str(e),
            }


# class AgentService:
#     def __init__(self):
#         self.agent_runner = AgentRunner()

#     async def run_agent(self, request: AgentRequest):
#         user_message = request.user_message
#         try:
#             result = await self.agent_runner.run(user_message)
#             logger.info(f"Agent response: {result}")
#         except Exception as e:
#             logger.error(f"Error: {e}")
#             raise RuntimeError("Agent request failed.") from e

#         return result

#     async def stream_agent(self, request: AgentRequest) -> AsyncIterator[str]:
#         """SSE를 위한 스트리밍 실행"""
#         user_message = request.user_message

#         try:
#             async for event in self.agent_runner.stream(user_message):
#                 # SSE 형식으로 데이터 전송
#                 data = json.dumps(event, ensure_ascii=False, default=str)
#                 yield f"data: {data}\n\n"
#         except Exception as e:
#             logger.error(f"Streaming error: {e}")
#             error_data = json.dumps(
#                 {"type": "error", "error": str(e)}, ensure_ascii=False
#             )
#             yield f"data: {error_data}\n\n"
