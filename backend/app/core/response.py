"""
API 응답 표준화 모델
- 일관된 API 응답 형식을 위한 Pydantic 모델 정의
- CommonResponse: 제네릭 타입을 지원하는 성공/실패 응답 래퍼
- ErrorResponse: 에러 전용 응답 모델
- success/fail_response 클래스 메서드로 간편한 응답 생성

사용 예시:
- 성공: CommonResponse.success_response("조회 성공", data)
- 실패: CommonResponse.fail_response("오류 발생")
- 에러: ErrorResponse.fail_response("에러 메시지")

# example1
@app.get(
    "/example",
    response_model=CommonResponse[ItemResponseModel],
    status_code=status.HTTP_200_OK,
)
async def get_item():
    data = ItemResponseModel(...)
    return CommonResponse.success_response("성공", data)


# example2
@router.get(
    "/user/info",
    response_model=CommonResponse[UserInfoResponse],
)
async def user_info_endpoint(user_id: int):
    result = service.get_user_info(user_id)
    return CommonResponse.success_response("조회 성공", UserInfoResponse(**result))


# router에 에러 응답 형식 정의 예시
router = APIRouter(
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Bad Request",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error",
        },
    },
)

"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class CommonResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None

    @classmethod
    def success_response(cls, message: str, data: Optional[T] = None):
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail_response(cls, message: str, data: Optional[T] = None):
        return cls(success=False, message=message, data=data)


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    data: Optional[Any] = None

    @classmethod
    def fail_response(cls, message: str, data: Optional[Any] = None):
        return cls(message=message, data=data)
