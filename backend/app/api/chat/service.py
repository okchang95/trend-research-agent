import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import AsyncIterator, Dict

from bson import ObjectId
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from app.agents.runner import AgentRunner
from app.api.chat.repository import ChatMessageRepository, ChatThreadRepository
from app.api.chat.schemas import ChatRequest, ChatThreadResponse, ChatMessageResponse
from app.api.chat.models import ChatThread, ChatMessage, MessageRole
from app.core.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class ChatThreadService:
    """
    Thread CRUD Service
    """

    def __init__(self, repo: ChatThreadRepository):
        self._repo = repo

    async def get_threads(self):
        threads = await self._repo.get_all()
        if not threads:
            return []
        return [
            ChatThreadResponse(
                thread_id=str(thread["_id"]),
                title=thread["title"],
                created_at=thread["created_at"],
                updated_at=thread["updated_at"],
            )
            for thread in threads
        ]


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
        2) 필요 시 이전 대화내역 정리 (short term memory)
        3) 에이전트 호출 (대화내역 전달, 스트리밍)
        4) 메세지 저장 (user_message, assistant_message)
        5) 대화 buffer 업데이트 (thread conversations)
        6) thread title update (if first message, update title)
        """
        user_id = payload.user_id
        user_message = payload.user_message
        requested_at = datetime.now(tz=ZoneInfo("Asia/Seoul"))

        logger.info(f"Received request for user_id: {user_id}")

        # --------------------------------------------------------------------------------------------
        # 1. 스레드 조회
        # --------------------------------------------------------------------------------------------
        thread: dict = await self._repo_chat_thread.get_by_user_id(user_id)
        is_new_thread = False

        if not thread:
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
            thread_id = str(thread["_id"])

        # 스레드 ID 전송
        yield {
            "type": "thread",
            "thread_id": thread_id,
            "title": thread.get("title", "New Thread"),
        }

        # --------------------------------------------------------------------------------------------
        # 2. last_summarized_at 이후의 메세지 조회 (short term memory)
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
        # 3. 에이전트 실행
        # --------------------------------------------------------------------------------------------
        final_answer = None
        current_node = None
        report_summary = None

        try:
            # 에이전트 스트리밍 실행
            async for event in self.agent_runner.stream(
                user_message=user_message,
                conversations=unsummarized_messages,
                conversations_summary=conversations_summary,
            ):
                # final 이벤트에서 answer와 current_node 추출
                if event.get("type") == "final":
                    state = event.get("state", {})
                    final_answer = state.get("answer", "")
                    current_node = state.get("current_node", "")

                yield event

            # 최종 메시지 생성이 writer 노드인 경우 보고서 요약
            if final_answer:
                if current_node == "writer":
                    report_summary = await self._summarize_report(final_answer)

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "type": "error",
                "error": str(e),
            }
            final_answer = "error"

        generated_at = datetime.now(tz=ZoneInfo("Asia/Seoul"))

        # --------------------------------------------------------------------------------------------
        # 4. 메세지 저장 (user_message, assistant_message)
        # --------------------------------------------------------------------------------------------
        user_message_obj = ChatMessage(
            thread_id=thread_id,
            role=MessageRole.USER,
            ended_node=current_node,
            message=user_message,
            timestamp=requested_at,
        )
        user_message_obj = user_message_obj.model_dump()
        user_message_obj["thread_id"] = ObjectId(thread_id)
        await self._repo_chat_message.create(user_message_obj)

        assistant_message_obj = ChatMessage(
            thread_id=thread_id,
            role=MessageRole.ASSISTANT,
            ended_node=current_node,
            message=final_answer,
            report_summary=report_summary,
            timestamp=generated_at,
        )
        assistant_message_obj = assistant_message_obj.model_dump()
        assistant_message_obj["thread_id"] = ObjectId(thread_id)
        await self._repo_chat_message.create(assistant_message_obj)

        # --------------------------------------------------------------------------------------------
        # 5. 대화 요약 업데이트 (thread conversation_summary)
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
        # 6. thread title update (if first message, update title)
        # --------------------------------------------------------------------------------------------
        conversations = []

        # 첫 메세지인 경우 스레드 제목 생성
        if is_new_thread:
            conversations = [
                {"role": "user", "message": user_message},
                {"role": "assistant", "message": final_answer},
            ]
        # 보고서 작성 완료 후 스레드 제목 업데이트
        elif current_node == "writer":
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

        if conversations:
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
