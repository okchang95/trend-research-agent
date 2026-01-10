import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import AsyncIterator, Dict

from bson import ObjectId
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from app.agents.runner import AgentRunner
from app.api.chat.repository import ChatMessageRepository, ChatThreadRepository
from app.api.chat.schemas import (
    ChatRequest,
    ChatThreadCreate,
    ChatThreadResponse,
    ChatMessageResponse,
)
from app.api.chat.models import ChatThread, ChatMessage, MessageRole, ThreadStatus
from app.core.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class ChatThreadService:
    """
    Thread CRUD Service
    """

    def __init__(self, repo: ChatThreadRepository):
        self._repo = repo

    async def get_threads(self, user_id: str):
        threads = await self._repo.get_all_by_user_id(user_id)
        if not threads:
            return []
        return [
            ChatThreadResponse(
                thread_id=str(thread["_id"]),
                title=thread["title"],
                status=thread.get("status", ThreadStatus.IDLE),
                created_at=thread["created_at"],
                updated_at=thread["updated_at"],
            )
            for thread in threads
        ]

    async def create_thread(self, payload: ChatThreadCreate):
        requested_at = datetime.now(tz=ZoneInfo("Asia/Seoul"))
        user_id = payload.user_id
        thread = ChatThread(
            user_id=user_id,
            title="New Thread",
            created_at=requested_at,
            updated_at=requested_at,
        ).model_dump()
        thread["user_id"] = ObjectId(user_id)

        thread_id = await self._repo.create(thread)

        return ChatThreadResponse(
            thread_id=str(thread_id),
            title=thread["title"],
            status=thread.get("status", ThreadStatus.IDLE),
            created_at=thread["created_at"],
            updated_at=thread["updated_at"],
        )


class ChatMessageService:
    """
    Message CRUD Service
    """

    def __init__(self, repo: ChatMessageRepository):
        self._repo = repo

    async def get_messages_by_thread_id(self, thread_id: str):
        messages = await self._repo.get_by_thread_id(thread_id)
        if not messages:
            return []
        return [
            ChatMessageResponse(
                message_id=str(message["_id"]),
                thread_id=str(message["thread_id"]),
                role=message["role"],
                message=message["message"],
                findings=message.get("findings", None),
                timestamp=message["timestamp"],
            )
            for message in messages
        ]


class ChatService:
    """
    Chat Agent Streaming Service
    """

    def __init__(
        self,
        _repo_chat_message: ChatMessageRepository,
        _repo_chat_thread: ChatThreadRepository,
    ):
        self.agent_runner = AgentRunner()
        self._repo_chat_message = _repo_chat_message
        self._repo_chat_thread = _repo_chat_thread

    async def stream_conversation(self, payload: ChatRequest) -> AsyncIterator[Dict]:
        """
        SSE를 위한 스트리밍 대화
        각 노드의 실행 결과와 최종 텍스트를 스트리밍으로 전송

        Sequence:
        - 메세지 타이핑 후 "전송"버튼 클릭 시,
        1) thread 조회(대화내역 포함), 없으면 생성
        2) 메세지 저장 (user_message)
        3) 제목 생성 (if first message)
        4) last_summarized_at 이후의 메세지 조회 (short term memory)
        5) 에이전트 실행
        6) 메세지 저장 (assistant_message)
        7) 대화 요약 업데이트 (thread conversation_summary)
        8) thread title update (if report generated)
        """
        user_id = payload.user_id
        thread_id = payload.thread_id
        user_message = payload.user_message
        requested_at = datetime.now(tz=ZoneInfo("Asia/Seoul"))

        logger.info(f"Received request for user_id: {user_id}")

        # --------------------------------------------------------------------------------------------
        # 1. 스레드 조회
        # --------------------------------------------------------------------------------------------
        is_new_thread = False

        if not thread_id:
            is_new_thread = True
            thread = ChatThread(
                user_id=user_id,
                title="New Thread",
                created_at=requested_at,
                updated_at=requested_at,
            ).model_dump()
            thread["user_id"] = ObjectId(user_id)
            thread_id = await self._repo_chat_thread.create(thread)
            thread["_id"] = thread_id
        else:
            thread = await self._repo_chat_thread.get_by_oid(thread_id)

        # 스레드 ID 전송
        yield {
            "type": "thread",
            "thread_id": thread_id,
            "title": thread.get("title", "New Thread"),
        }

        # --------------------------------------------------------------------------------------------
        # 2. 메세지 저장 (user_message)
        # --------------------------------------------------------------------------------------------
        user_message_obj = ChatMessage(
            thread_id=thread_id,
            role=MessageRole.USER,
            ended_node=None,
            message=user_message,
            timestamp=requested_at,
        )
        user_message_obj = user_message_obj.model_dump()
        user_message_obj["thread_id"] = ObjectId(thread_id)
        await self._repo_chat_message.create(user_message_obj)

        # --------------------------------------------------------------------------------------------
        # 3. 제목 생성 (if first message)
        # --------------------------------------------------------------------------------------------
        # 첫 메시지인 경우 user_message만으로 제목 생성 (agent 실행 전)
        if is_new_thread:
            thread_title = await self._generate_thread_title(
                [{"role": "user", "message": user_message}]
            )
            await self._repo_chat_thread.update(
                thread_id,
                {"title": thread_title, "updated_at": requested_at},
            )
            yield {
                "type": "thread",
                "thread_id": thread_id,
                "title": thread_title,
            }
        # --------------------------------------------------------------------------------------------
        # 4. last_summarized_at 이후의 메세지 조회 (short term memory)
        # --------------------------------------------------------------------------------------------
        unsummarized_messages = (
            await self._repo_chat_message.get_unsummarized_by_thread_id(
                thread_id=thread_id,
                last_summarized_at=thread.get("last_summarized_at"),
            )
        )
        # report_summary가 있고 ended_node가 writer인 경우 report_summary를 사용, 아니면 message를 사용
        unsummarized_messages = (
            [
                {
                    "role": msg["role"],
                    "message": (
                        msg.get("report_summary")
                        if msg.get("report_summary")
                        and msg.get("ended_node") == "writer"
                        else msg.get("message", "")
                    ),
                    "timestamp": msg["timestamp"],
                }
                for msg in unsummarized_messages
            ]
            if unsummarized_messages
            else []
        )

        conversations_summary = thread.get("conversation_summary", "")

        # --------------------------------------------------------------------------------------------
        # 5. 에이전트 실행
        # --------------------------------------------------------------------------------------------
        final_answer = None
        current_node = None
        report_summary = None
        findings = None

        # Thread 상태를 GENERATING으로 변경
        await self._repo_chat_thread.update(
            thread_id,
            {"status": ThreadStatus.GENERATING, "updated_at": requested_at},
        )

        try:
            # 에이전트 스트리밍 실행
            async for event in self.agent_runner.stream(
                user_message=user_message,
                conversations=unsummarized_messages,
                conversations_summary=conversations_summary,
            ):
                # final 이벤트에서 answer, current_node, findings 추출
                if event.get("type") == "final":
                    state = event.get("state", {})
                    final_answer = state.get("answer", "")
                    current_node = state.get("current_node", "")
                    findings = state.get("findings", None)

                yield event

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "type": "error",
                "error": str(e),
            }
            final_answer = "error"

        finally:
            # 연결이 끊겨도 final_answer가 있으면 반드시 저장
            if final_answer:
                try:
                    generated_at = datetime.now(tz=ZoneInfo("Asia/Seoul"))

                    # 최종 메시지 생성이 writer 노드인 경우 보고서 요약
                    if current_node == "writer":
                        report_summary = await self._summarize_report(final_answer)

                    # --------------------------------------------------------------------------------------------
                    # 6. 메세지 저장 (assistant_message)
                    # --------------------------------------------------------------------------------------------
                    assistant_message_obj = ChatMessage(
                        thread_id=thread_id,
                        role=MessageRole.ASSISTANT,
                        ended_node=current_node,
                        message=final_answer,
                        report_summary=report_summary,
                        findings=findings,
                        timestamp=generated_at,
                    )
                    assistant_message_obj = assistant_message_obj.model_dump()
                    assistant_message_obj["thread_id"] = ObjectId(thread_id)
                    await self._repo_chat_message.create(assistant_message_obj)
                    logger.info(f"Assistant message saved for thread {thread_id}")

                    # --------------------------------------------------------------------------------------------
                    # 7. 대화 요약 업데이트 (thread conversation_summary)
                    # --------------------------------------------------------------------------------------------
                    UNSUMMARIZED_THRESHOLD = 20
                    RECENT_COUNT = 12
                    total_unsummarized_after_turn = len(unsummarized_messages) + 2

                    # 요약되지 않은 메세지가 20개 이상일때, 최근 12개의 메세지를 제외한 8개의 메세지와 요약 내용을 업데이트
                    if total_unsummarized_after_turn >= UNSUMMARIZED_THRESHOLD:
                        # 요약할 메시지가 충분한지 확인
                        messages_to_summarize = (
                            unsummarized_messages[:-RECENT_COUNT]
                            if len(unsummarized_messages) >= RECENT_COUNT
                            else []
                        )

                        # 요약할 메시지가 있을 때 요약 진행
                        if messages_to_summarize:
                            logger.info("Updating conversation summary")
                            new_summary = await self._summarize_context(
                                conversations=messages_to_summarize,
                                conversations_summary=conversations_summary,
                            )

                            await self._repo_chat_thread.update(
                                thread_id,
                                {
                                    "conversation_summary": new_summary,
                                    "last_summarized_at": generated_at,
                                    "updated_at": generated_at,
                                },
                            )
                        else:
                            await self._repo_chat_thread.update(
                                thread_id,
                                {"updated_at": generated_at},
                            )
                    else:
                        await self._repo_chat_thread.update(
                            thread_id,
                            {"updated_at": generated_at},
                        )

                    # --------------------------------------------------------------------------------------------
                    # 8. thread title update (if report generated)
                    # --------------------------------------------------------------------------------------------
                    # 보고서 작성 완료 후 스레드 제목 업데이트
                    if current_node == "writer":
                        conversations = []

                        # unsummarized_messages가 있으면 포함
                        conversations = (
                            [
                                {"role": msg["role"], "message": msg["message"]}
                                for msg in unsummarized_messages
                            ]
                            if unsummarized_messages
                            else []
                        )

                        # 현재 턴의 메시지 추가
                        conversations.extend(
                            [
                                {
                                    "role": "user",
                                    "message": user_message,
                                },
                                {
                                    "role": "assistant",
                                    "message": report_summary or final_answer or "",
                                },
                            ]
                        )

                        thread_title = await self._generate_thread_title(conversations)
                        await self._repo_chat_thread.update(
                            thread_id,
                            {"title": thread_title, "updated_at": generated_at},
                        )
                        yield {
                            "type": "thread",
                            "thread_id": thread_id,
                            "title": thread_title,
                        }

                    # Thread 상태를 COMPLETED 또는 ERROR로 업데이트
                    final_status = (
                        ThreadStatus.ERROR
                        if final_answer == "error"
                        else ThreadStatus.COMPLETED
                    )
                    await self._repo_chat_thread.update(
                        thread_id,
                        {"status": final_status},
                    )

                except Exception as save_error:
                    logger.error(f"Failed to save assistant message: {save_error}")
                    # 저장 실패 시 에러 상태로 변경
                    await self._repo_chat_thread.update(
                        thread_id,
                        {"status": ThreadStatus.ERROR},
                    )
            else:
                # final_answer가 없으면 (중단된 경우) IDLE 상태로 복귀
                await self._repo_chat_thread.update(
                    thread_id,
                    {"status": ThreadStatus.IDLE},
                )

    ############################################################################################
    #
    # llm utils
    # - generate thread title
    # - summarize context
    # - summarize report
    #
    ############################################################################################
    async def _generate_thread_title(self, message_history: list):
        llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0.4, api_key=config.OPENAI_API_KEY
        )
        template = """
        You are a helpful assistant that generates chat thread titles.
        You are given message history of a chat thread.
        You need to generate a thread title based on the message history.

        <Message History>
        {message_history}
        </Message History>

        Return the thread title only.
        Thread title:
        """
        prompt = PromptTemplate(
            template=template.replace("  ", "").strip(),
            input_variables=["message_history"],
        )
        chain = prompt | llm
        result = await chain.ainvoke({"message_history": message_history})
        logger.info(f"Thread title generated: {result.content}")
        return result.content

    async def _summarize_context(self, conversations, conversations_summary):
        llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY
        )
        template = """
        You are a helpful assistant that summarizes conversations.
        You are given a conversation and a context summary before conversations.
        You need to summarize the conversation and update the context summary.

        <Context Summary>
        {conversations_summary}
        </Context Summary>

        <Conversation>
        {conversation}
        </Conversation>

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
        logger.info(f"Context summarized: {result.content}")
        return result.content

    async def _summarize_report(self, report: str):
        llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY
        )
        template = """ 
        You are a helpful assistant that summarizes reports.
        You are given a report and you need to summarize the report.
        Summarize the report in 1000 characters or less.
        And mention it is report summary.

        <Report>
        {report}
        </Report>

        Return the summarized report only.
        Summarized report:
        """
        chain = PromptTemplate(template=template.replace("  ", "").strip()) | llm
        result = await chain.ainvoke({"report": report})
        logger.info(f"Report summarized: {result.content}")
        return result.content

    async def save_cancelled_message(self, payload: dict):
        """
        스트림 중지 시 부분 응답 저장
        """
        thread_id = payload.get("thread_id")
        user_id = payload.get("user_id")
        partial_message = payload.get("partial_message", "")

        if not thread_id or not user_id:
            raise ValueError("thread_id and user_id are required")

        generated_at = datetime.now(tz=ZoneInfo("Asia/Seoul"))

        # "응답 중지됨" 메시지 생성
        if partial_message:
            cancelled_message = (
                f"{partial_message}\n\n---\n\n**[응답이 중지되었습니다]**"
            )
        else:
            cancelled_message = "**[응답이 중지되었습니다]**"

        # Assistant 메시지 저장
        assistant_message_obj = ChatMessage(
            thread_id=thread_id,
            role=MessageRole.ASSISTANT,
            ended_node="cancelled",  # 특별한 상태 표시
            message=cancelled_message,
            timestamp=generated_at,
        )
        assistant_message_obj = assistant_message_obj.model_dump()
        assistant_message_obj["thread_id"] = ObjectId(thread_id)
        message_id = await self._repo_chat_message.create(assistant_message_obj)

        # Thread updated_at 및 status 업데이트 (IDLE로 복귀)
        await self._repo_chat_thread.update(
            thread_id,
            {"updated_at": generated_at, "status": ThreadStatus.IDLE},
        )

        logger.info(f"Cancelled message saved for thread {thread_id}")

        return {
            "message_id": str(message_id),
            "thread_id": thread_id,
        }
