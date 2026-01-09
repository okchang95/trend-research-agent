from fastapi import APIRouter, Depends
from fastapi import HTTPException

from app.api.threads.deps import get_thread_service
from app.api.threads.service import ThreadService
from app.core.response import CommonResponse, ErrorResponse

router = APIRouter()


@router.get("/threads")
async def get_threads(
    service: ThreadService = Depends(get_thread_service),
):
    try:
        result = await service.get_threads()
        return CommonResponse.success_response(
            message="Threads retrieved successfully",
            data=result,
        )
    except HTTPException as e:
        return CommonResponse.fail_response(message=e.detail)
    except Exception as e:
        return ErrorResponse.fail_response(message=str(e))
