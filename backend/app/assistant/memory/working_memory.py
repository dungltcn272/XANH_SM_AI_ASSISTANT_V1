from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Message


def get_recent_turns(db: Session, conversation_id: str | None, limit: int = 12) -> list[dict[str, str]]:
    if not conversation_id:
        return []
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    return [{"role": row.role, "content": row.content} for row in reversed(rows)]
