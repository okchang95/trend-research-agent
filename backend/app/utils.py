from datetime import datetime


def date_to_str_recursive(obj: dict) -> dict:
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, list):
        return [date_to_str_recursive(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: date_to_str_recursive(value) for key, value in obj.items()}
    return obj
