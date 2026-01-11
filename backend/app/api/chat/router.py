from fastapi import APIRouter, Depends, HTTPException

from app.api.chat.deps import (
    get_chat_service,
    get_chat_thread_service,
    get_chat_message_service,
)
from app.api.chat.schemas import (
    ChatRequest,
    ChatThreadCreate,
    ChatThreadResponse,
    CancelRequest,
)
from app.api.chat.service import (
    ChatService,
    ChatThreadService,
    ChatMessageService,
)
from app.api.chat.sse import create_sse_response
from app.core.response import CommonResponse, ErrorResponse

router = APIRouter()


############################################################
#
# Chat Agent Controllers
#
############################################################
@router.post("/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    """
    SSE를 통한 스트리밍 채팅
    각 노드의 실행 결과와 최종 텍스트를 실시간으로 전송
    """
    event_generator = service.stream_conversation(payload)
    return create_sse_response(event_generator)


@router.post("/chat/cancel")
async def cancel_chat(
    payload: CancelRequest,
    service: ChatService = Depends(get_chat_service),
):
    """
    스트림 중지 시 부분 응답 저장
    """
    try:
        result = await service.save_cancelled_message(payload.model_dump())
        return CommonResponse.success_response(
            message="Cancelled message saved successfully",
            data=result,
        )
    except HTTPException as e:
        return CommonResponse.fail_response(message=e.detail)
    except Exception as e:
        return ErrorResponse.fail_response(message=str(e))


@router.post("/chat/cancel-task")
async def cancel_task(
    payload: dict,
    service: ChatService = Depends(get_chat_service),
):
    """
    진행 중인 백그라운드 agent task 취소
    """
    try:
        thread_id = payload.get("thread_id")
        if not thread_id:
            return CommonResponse.fail_response(message="thread_id required")

        cancelled = await service.cancel_stream(thread_id)

        if cancelled:
            return CommonResponse.success_response(
                message="Task cancelled successfully",
                data={"thread_id": thread_id},
            )
        else:
            return CommonResponse.success_response(
                message="No active task found",
                data={"thread_id": thread_id},
            )
    except HTTPException as e:
        return CommonResponse.fail_response(message=e.detail)
    except Exception as e:
        return ErrorResponse.fail_response(message=str(e))


############################################################
#
# Threads Controllers
# 1. GET threads list
# 2. POST create new thread
# TODO: 3. Update thread title
# TODO: 4. Delete thread
#
############################################################
@router.get("/threads")
async def get_threads(
    user_id: str,
    service: ChatThreadService = Depends(get_chat_thread_service),
):
    try:
        result = await service.get_threads(user_id)
        return CommonResponse.success_response(
            message="Threads retrieved successfully",
            data=result,
        )
    except HTTPException as e:
        return CommonResponse.fail_response(message=e.detail)
    except Exception as e:
        return ErrorResponse.fail_response(message=str(e))


@router.post("/threads")
async def create_thread(
    payload: ChatThreadCreate,
    service: ChatThreadService = Depends(get_chat_thread_service),
):
    try:
        result = await service.create_thread(payload)
        return CommonResponse.success_response(
            message="Thread created successfully",
            data=result,
        )
    except HTTPException as e:
        return CommonResponse.fail_response(message=e.detail)
    except Exception as e:
        return ErrorResponse.fail_response(message=str(e))


############################################################
#
# Messages Controllers
# 1. GET messages in thread by thread_id
#
############################################################
@router.get("/threads/{thread_id}/messages")
async def get_messages_by_thread_id(
    thread_id: str,
    user_id: str,
    message_service: ChatMessageService = Depends(get_chat_message_service),
    thread_service: ChatThreadService = Depends(get_chat_thread_service),
):
    try:
        # Thread 소유권 검증
        try:
            thread = await thread_service.get_thread_by_id(thread_id, user_id)
            if not thread:
                return CommonResponse.fail_response(message="Thread not found")
        except ValueError as e:
            return CommonResponse.fail_response(message=str(e))
        
        # 권한이 확인되면 메시지 조회
        result = await message_service.get_messages_by_thread_id(thread_id)
        return CommonResponse.success_response(
            message="Messages retrieved successfully",
            data=result,
        )
    except HTTPException as e:
        return CommonResponse.fail_response(message=e.detail)
    except Exception as e:
        return ErrorResponse.fail_response(message=str(e))
