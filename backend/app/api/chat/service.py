import asyncio
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
        # Task 저장소: thread_id -> asyncio.Task
        self._active_tasks: dict[str, asyncio.Task] = {}

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
        # 5. 에이전트 실행 (비동기 + 큐 패턴)
        # --------------------------------------------------------------------------------------------
        # Thread 상태를 GENERATING으로 변경
        await self._repo_chat_thread.update(
            thread_id,
            {"status": ThreadStatus.GENERATING, "updated_at": requested_at},
        )

        # 이벤트를 공유할 Queue
        event_queue = asyncio.Queue()

        # 백그라운드에서 agent 실행 (이벤트를 queue에 넣고 + DB에 저장)
        background_task = asyncio.create_task(
            self._run_agent_and_save(
                thread_id=thread_id,
                user_message=user_message,
                unsummarized_messages=unsummarized_messages,
                conversations_summary=conversations_summary,
                event_queue=event_queue,
            )
        )

        # Task 등록 (중지 기능을 위해)
        self._active_tasks[thread_id] = background_task

        try:
            # Queue에서 이벤트를 읽어서 SSE로 전송
            while True:
                event = await event_queue.get()

                # 종료 신호
                if event is None:
                    break

                yield event

        except GeneratorExit:
            # 클라이언트 연결 끊김 (새로고침, 페이지 이탈 등)
            # background_task는 계속 실행되어 DB에 저장
            logger.info(
                f"Client disconnected, but agent continues in background for thread {thread_id}"
            )
            raise

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "type": "error",
                "error": str(e),
            }

        finally:
            # Task가 아직 실행 중이면 완료 대기는 하지 않음 (백그라운드에서 계속 실행)
            if not background_task.done():
                logger.info(
                    f"Background task continues for thread {thread_id} (client disconnected)"
                )
            else:
                # Task가 완료되었으면 예외 확인 및 제거
                try:
                    await background_task
                except Exception as task_error:
                    logger.error(f"Background task error: {task_error}")
                finally:
                    # Task 제거
                    self._active_tasks.pop(thread_id, None)

    async def _run_agent_and_save(
        self,
        thread_id: str,
        user_message: str,
        unsummarized_messages: list,
        conversations_summary: str,
        event_queue: asyncio.Queue,
    ):
        """
        백그라운드에서 실행되는 agent
        - Agent를 한 번만 실행
        - 각 이벤트를 queue에 넣음 (SSE streaming용)
        - 최종 결과를 DB에 저장 (연결 끊겨도 실행)
        """
        final_answer = None
        current_node = None
        findings = None
        report_summary = None

        try:
            # Agent는 딱 한 번만 실행!
            async for event in self.agent_runner.stream(
                user_message=user_message,
                conversations=unsummarized_messages,
                conversations_summary=conversations_summary,
            ):
                # 이벤트를 queue에 넣음 (SSE로 전송될 수 있도록)
                try:
                    await event_queue.put(event)
                except Exception as e:
                    # Queue가 닫혔거나 에러 - 클라이언트가 끊긴 것
                    logger.warning(f"Failed to put event in queue: {e}")

                # Final 이벤트 추출
                if event.get("type") == "final":
                    state = event.get("state", {})
                    final_answer = state.get("answer", "")
                    current_node = state.get("current_node", "")
                    findings = state.get("findings", None)

            # 종료 신호 전송
            await event_queue.put(None)

            # --------------------------------------------------------------------------------------------
            # DB에 저장 (연결 끊겨도 실행됨!)
            # --------------------------------------------------------------------------------------------
            if final_answer:
                generated_at = datetime.now(tz=ZoneInfo("Asia/Seoul"))

                # 최종 메시지 생성이 writer 노드인 경우 보고서 요약
                if current_node == "writer":
                    report_summary = await self._summarize_report(final_answer)

                # Assistant 메시지 저장
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

                # 대화 요약 업데이트
                UNSUMMARIZED_THRESHOLD = 20
                RECENT_COUNT = 12
                total_unsummarized_after_turn = len(unsummarized_messages) + 2

                if total_unsummarized_after_turn >= UNSUMMARIZED_THRESHOLD:
                    messages_to_summarize = (
                        unsummarized_messages[:-RECENT_COUNT]
                        if len(unsummarized_messages) >= RECENT_COUNT
                        else []
                    )

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

                # Thread 제목 업데이트 (writer 노드인 경우)
                if current_node == "writer":
                    conversations = (
                        [
                            {"role": msg["role"], "message": msg["message"]}
                            for msg in unsummarized_messages
                        ]
                        if unsummarized_messages
                        else []
                    )

                    conversations.extend(
                        [
                            {"role": "user", "message": user_message},
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

                    # Thread 제목 업데이트 이벤트 전송 (클라이언트가 아직 연결되어 있다면)
                    try:
                        await event_queue.put(
                            {
                                "type": "thread",
                                "thread_id": thread_id,
                                "title": thread_title,
                            }
                        )
                    except Exception:
                        pass  # 클라이언트가 끊김

                # Thread 상태를 COMPLETED로 업데이트
                await self._repo_chat_thread.update(
                    thread_id,
                    {"status": ThreadStatus.COMPLETED},
                )

                logger.info(f"✅ Agent completed and saved for thread {thread_id}")
            else:
                # Agent가 final까지 가지 못함
                await self._repo_chat_thread.update(
                    thread_id,
                    {"status": ThreadStatus.IDLE},
                )
                logger.warning(
                    f"Agent did not reach final state for thread {thread_id}"
                )

        except asyncio.CancelledError:
            # Task가 취소됨 (중지 버튼)
            logger.info(f"Agent task cancelled for thread {thread_id}")

            # 종료 신호 전송
            try:
                await event_queue.put(None)
            except Exception:
                pass

            # Thread를 IDLE로 변경
            await self._repo_chat_thread.update(
                thread_id,
                {"status": ThreadStatus.IDLE},
            )

            # Task 제거
            # (이미 취소되었으므로 _active_tasks에서 제거 - cancel_stream에서 처리)

            raise  # CancelledError는 재발생시켜야 함

        except Exception as e:
            logger.error(f"Background agent error for thread {thread_id}: {e}")

            # 에러 신호 전송
            try:
                await event_queue.put(
                    {
                        "type": "error",
                        "error": str(e),
                    }
                )
                await event_queue.put(None)
            except Exception:
                pass  # Queue 에러 무시

            # Thread status를 ERROR로
            await self._repo_chat_thread.update(
                thread_id,
                {"status": ThreadStatus.ERROR},
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

    async def cancel_stream(self, thread_id: str) -> bool:
        """
        진행 중인 agent task를 취소
        
        Args:
            thread_id: 취소할 thread의 ID
            
        Returns:
            bool: Task가 취소되었으면 True, 실행 중인 task가 없으면 False
        """
        task = self._active_tasks.get(thread_id)

        if task and not task.done():
            # Task 취소
            task.cancel()
            logger.info(f"Cancelled background task for thread {thread_id}")

            # Task 제거
            self._active_tasks.pop(thread_id, None)

            # Thread status를 IDLE로 변경 (CancelledError 핸들러에서도 처리하지만 여기서도 보장)
            try:
                await self._repo_chat_thread.update(
                    thread_id,
                    {"status": ThreadStatus.IDLE},
                )
            except Exception as e:
                logger.error(f"Failed to update thread status: {e}")

            return True

        return False
