from __future__ import annotations

import json
from typing import Any

from app.core.logger import log_warn
from app.db.models import SystemLog


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
                )
            )
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        log_warn("SYSTEM_LOG", f"Failed to save system log: {exc}")
