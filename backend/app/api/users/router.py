from fastapi import APIRouter, Depends
from fastapi import HTTPException

from app.api.users.deps import get_user_service
from app.api.users.schemas import UserCreate
from app.api.users.service import UserService
from app.core.response import CommonResponse, ErrorResponse

router = APIRouter()


@router.post("/users")
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
):
    try:
        result = await service.create_user(payload)
        return CommonResponse.success_response(
            message="User created successfully",
            data=result,
        )
    except HTTPException as e:
        return CommonResponse.fail_response(message=e.detail)
    except Exception as e:
        return CommonResponse.fail_response(message=str(e))


@router.get("/users")
async def get_user_by_name(
    name: str,
    service: UserService = Depends(get_user_service),
):
    try:
        result = await service.get_user_by_name(name)
        return CommonResponse.success_response(
            message="User retrieved successfully",
            data=result,
        )
    except HTTPException as e:
        return CommonResponse.fail_response(message=e.detail)
    except Exception as e:
        return ErrorResponse.fail_response(message=str(e))
