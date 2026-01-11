"""
SSE (Server-Sent Events) 관련 유틸리티 모듈
"""
import json
from typing import AsyncIterator, Dict

from fastapi.responses import StreamingResponse


def create_sse_response(event_generator: AsyncIterator[Dict]) -> StreamingResponse:
    """
    SSE 응답 생성
    
    Args:
        event_generator: 이벤트를 생성하는 async iterator
        
    Returns:
        StreamingResponse: SSE 형식의 스트리밍 응답
    """
    async def sse_event_generator():
        try:
            async for event in event_generator:
                # SSE 형식으로 데이터 전송
                data = json.dumps(event, ensure_ascii=False, default=str)
                yield f"data: {data}\n\n"
        except Exception as e:
            error_data = json.dumps(
                {"type": "error", "error": str(e)}, ensure_ascii=False
            )
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

