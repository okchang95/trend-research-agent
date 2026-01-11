from datetime import datetime
from typing import Any

from bson import ObjectId
from pydantic import BaseModel


def recursive_model_dump(obj: Any, dt_serialize: bool = True):
    """
    Recursively dumps Pydantic objects (BaseModel) to dictionaries,
    including handling nested lists, dictionaries, and datetime serialization.
    """
    if isinstance(obj, BaseModel):  # If it's a Pydantic model, dump it
        return recursive_model_dump(obj.model_dump(), dt_serialize=dt_serialize)
    elif isinstance(obj, dict):  # If it's a dictionary, process each key-value pair
        return {
            key: recursive_model_dump(value, dt_serialize=dt_serialize)
            for key, value in obj.items()
        }
    elif isinstance(obj, list):  # If it's a list, process each item
        return [recursive_model_dump(item, dt_serialize=dt_serialize) for item in obj]
    elif isinstance(obj, datetime) and dt_serialize:  # Serialize datetime to ISO format
        return obj.isoformat()
    else:  # If it's neither, return the object as is
        return obj


def recursive_str_to_oid(obj):
    """문자열 형태의 ObjectId를 재귀적으로 ObjectId 객체로 복원"""
    if isinstance(obj, dict):
        return {k: recursive_str_to_oid(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [recursive_str_to_oid(i) for i in obj]
    elif isinstance(obj, str) and ObjectId.is_valid(obj):
        return ObjectId(obj)
    return obj


def recursive_oid_to_str(data):
    if isinstance(data, list):
        return [recursive_oid_to_str(item) for item in data]
    if isinstance(data, dict):
        return {key: recursive_oid_to_str(value) for key, value in data.items()}
    if isinstance(data, ObjectId):
        return str(data)
    return data
