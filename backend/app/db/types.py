"""
데이터베이스 관련 커스텀 타입 정의
- MongoDB ObjectId를 위한 Pydantic 호환 타입
- JSON 직렬화/역직렬화 지원
- 타입 검증 및 변환 로직 포함
"""

from typing import Any

from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(str):
    """
    custom pydantic 타입, 24개의 16진수 문자열을 받아서 ObjectId로 변환
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(cls.validate),
                        ]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, value) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")

        return ObjectId(value)
