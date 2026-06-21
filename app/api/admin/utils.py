import json
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Callable

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

def _iso(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=VN_TZ)
        else:
            value = value.astimezone(VN_TZ)
    return value.isoformat()

def serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return _iso(value)
    return value

def parse_optional_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None

def _json_text_with_defaults(value: str | None, defaults: dict[str, Any]) -> str:
    try:
        data = json.loads(value or "{}")
        if not isinstance(data, dict):
            data = {}
    except json.JSONDecodeError:
        data = {}
    for key, fallback in defaults.items():
        data.setdefault(key, fallback(data) if callable(fallback) else fallback)
    return json.dumps(data, ensure_ascii=False)

def json_text(value: Any) -> str:
    if value is None:
        return "[]"
    return json.dumps(value, ensure_ascii=False)
