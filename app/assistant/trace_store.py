from __future__ import annotations

from app.core.logger import log_warn
from app.db.models import BasicRequestLog

def save_basic_request_log(
    *,
    conversation_id: str | None,
    user_id: str | None,
    guest_id: str | None,
    original_query: str,
    rewritten_query: str | None,
    intent: str | None,
    final_answer: str | None,
    nlu_latency_ms: float,
    total_latency_ms: float,
):
    try:
        from app.db.database import SessionLocal

        db = SessionLocal()
        try:
            log_entry = BasicRequestLog(
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                original_query=original_query,
                rewritten_query=rewritten_query,
                intent=intent,
                final_answer=final_answer,
                nlu_latency_ms=nlu_latency_ms,
                total_latency_ms=total_latency_ms,
            )
            db.add(log_entry)
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        log_warn("ORCHESTRATOR", f"Failed to save basic request log: {exc}")
