from __future__ import annotations

import json
from typing import Any

from app.core.logger import log_warn
from app.db.models import SystemLog, get_vn_time


def save_system_log(
    *,
    node: str,
    event: str,
    level: str = "INFO",
    trace_id: str | None = None,
    conversation_id: str | None = None,
    user_id: str | None = None,
    guest_id: str | None = None,
    query: str | None = None,
    intent: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    try:
        from app.db.database import SessionLocal

        db = SessionLocal()
        try:
            db.add(
                SystemLog(
                    trace_id=trace_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    guest_id=guest_id,
                    level=level,
                    node=node,
                    event=event,
                    query=query,
                    intent=intent,
                    payload_json=json.dumps(payload or {}, ensure_ascii=False, default=str),
                    created_at=get_vn_time(),
                )
            )
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        log_warn("SYSTEM_LOG", f"Failed to save system log: {exc}")


def log_stage(
    node: str,
    event: str,
    *,
    level: str = "INFO",
    trace_id: str | None = None,
    conversation_id: str | None = None,
    user_id: str | None = None,
    guest_id: str | None = None,
    query: str | None = None,
    intent: str | None = None,
    payload: dict[str, Any] | None = None,
    **extra: Any,
) -> None:
    """Small convenience wrapper for pipeline telemetry.

    Use this at each stage boundary instead of repeating save_system_log(...)
    argument plumbing across RAG/Food/NLU code.
    """
    merged_payload = dict(payload or {})
    merged_payload.update({key: value for key, value in extra.items() if value is not None})
    save_system_log(
        node=node,
        event=event,
        level=level,
        trace_id=trace_id,
        conversation_id=conversation_id,
        user_id=user_id,
        guest_id=guest_id,
        query=query,
        intent=intent,
        payload=merged_payload,
    )
