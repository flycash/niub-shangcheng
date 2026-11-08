import json
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any


REDACTED = "[REDACTED]"


def json_safe(value: Any, *, max_length: int = 0) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, str) and max_length > 0 and len(value) > max_length:
            return value[:max_length] + "...[truncated]"
        return value
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, BaseException):
        return f"{type(value).__name__}: {value}"
    if isinstance(value, Mapping):
        return {
            str(key): json_safe(item, max_length=max_length)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [
            json_safe(item, max_length=max_length) for item in value
        ]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            return json_safe(
                model_dump(mode="json"),
                max_length=max_length,
            )
        except Exception:
            pass
    try:
        return json_safe(dict(value), max_length=max_length)
    except (TypeError, ValueError):
        return str(value)[:max_length] if max_length > 0 else str(value)


def redact_payload(
    value: Any,
    *,
    redact_keys: Sequence[str],
    max_length: int,
) -> Any:
    normalized_keys = {key.lower() for key in redact_keys}

    def walk(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {
                str(key): (
                    REDACTED
                    if str(key).lower() in normalized_keys
                    else walk(child)
                )
                for key, child in item.items()
            }
        if isinstance(item, Sequence) and not isinstance(
            item, (str, bytes, bytearray)
        ):
            return [walk(child) for child in item]
        return json_safe(item, max_length=max_length)

    return walk(value)


def payload_text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(value)


def truncate_text(value: str, max_length: int) -> str:
    if max_length <= 0 or len(value) <= max_length:
        return value
    return value[:max_length] + "...[truncated]"
