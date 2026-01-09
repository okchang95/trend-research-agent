import logging
import uuid
from typing import AsyncIterator, Dict

from app.agents.runner import AgentRunner
from app.api.session import SessionManager

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.agent_runner = AgentRunner()

    async def conversation(self, session_id: str, user_message: str):
        session_id = self._ensure_session_id(session_id)
        session = SessionManager.get_or_create_session(session_id)
        conversations_summary = session.get("conversations_summary", "")

        SessionManager.add_message(session_id, "user", user_message)

        response = await self._run_agent(
            user_message=user_message,
            conversations=session.get("conversations", []),
            conversations_summary=conversations_summary,
        )

        assistant_message = response.get("answer", "")
        SessionManager.add_message(session_id, "assistant", assistant_message)

        await self._summarize_if_needed(
            session_id=session_id,
            session=session,
            conversations_summary=conversations_summary,
        )

        return {
            "assistant_message": assistant_message,
            "session_id": session_id,
        }

    def _ensure_session_id(self, session_id: str) -> str:
        if session_id:
            return session_id

        logger.info("No session_id provided. Creating new session.")
        new_session_id = str(uuid.uuid4())
        logger.info("New session_id: %s", new_session_id)
        return new_session_id

    async def _run_agent(
        self,
        user_message: str,
        conversations: list,
        conversations_summary: str,
    ) -> dict:
        try:
            return await self.agent_runner.run(
                user_message=user_message,
                conversations=conversations,
                conversations_summary=conversations_summary,
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"answer": "응답 실패"}

    async def _summarize_if_needed(
        self,
        session_id: str,
        session: dict,
        conversations_summary: str,
    ) -> None:
        conversations = session.get("conversations", [])
        if len(conversations) < 20:
            return

        old_conversations = conversations[:-12]
        recent_conversations = conversations[-12:]

        new_summized_conversations = await self._summarize_context(
            old_conversations, conversations_summary
        )
        SessionManager.set_conversations_summary(session_id, new_summized_conversations)
        SessionManager.update_messages(session_id, recent_conversations)

    async def _summarize_context(self, conversations, conversations_summary):
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import PromptTemplate
        from app.core.config import get_config

        config = get_config()
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

    async def _summarize_report(self, report: str):
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import PromptTemplate
        from app.core.config import get_config

        config = get_config()
        llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY
        )
        template = """
        You are a helpful assistant that summarizes reports.
        You are given a report and you need to summarize the report.
        Summarize the report in 300 characters or less.

        <Report>
        {report}
        </Report>

        Return the summarized report only.
        Summarized report:
        """
        chain = PromptTemplate(template=template.replace("  ", "").strip()) | llm
        result = await chain.ainvoke({"report": report})
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
        # session_id가 없으면 새로운 세션 생성
        session_id = self._ensure_session_id(session_id)

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
        current_node = None

        try:
            # 에이전트 스트리밍 실행
            async for event in self.agent_runner.stream(
                user_message=user_message,
                conversations=session.get("conversations", []),
                conversations_summary=conversations_summary,
            ):
                # final 이벤트에서 answer와 current_node 추출
                if event.get("type") == "final":
                    state = event.get("state", {})
                    final_answer = state.get("answer", "")
                    current_node = state.get("current_node", "")

                yield event

            # 최종 메시지 저장
            if final_answer:
                # writer 노드 완료 시 보고서 요약해서 저장
                if current_node == "writer":
                    try:
                        logger.info(
                            "Writer node completed. Summarizing report for session storage."
                        )
                        summarized_report = await self._summarize_report(final_answer)
                        SessionManager.add_message(
                            session_id, "assistant", summarized_report
                        )
                        logger.info(
                            f"Report summarized and saved. Original length: {len(final_answer)}, Summarized length: {len(summarized_report)}"
                        )
                    except Exception as e:
                        logger.error(f"Error summarizing report: {e}")
                        # 요약 실패 시 원본 저장
                        SessionManager.add_message(
                            session_id, "assistant", final_answer
                        )
                else:
                    # writer 노드가 아니면 원본 그대로 저장
                    SessionManager.add_message(session_id, "assistant", final_answer)

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "type": "error",
                "error": str(e),
            }
