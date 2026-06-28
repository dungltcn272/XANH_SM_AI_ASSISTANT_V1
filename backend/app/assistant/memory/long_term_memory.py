from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Memory


def get_scoped_memories(
    db: Session,
    *,
    actor_id: str | None,
    persona_id: str,
    scopes: tuple[str, ...],
    limit: int = 12,
) -> list[dict[str, object]]:
    if not actor_id:
        return []
    rows = (
        db.query(Memory)
        .filter(Memory.actor_id == actor_id, Memory.status == "active")
        .filter((Memory.persona_id == persona_id) | (Memory.persona_id.is_(None)))
        .filter(Memory.scope.in_(scopes))
        .order_by(Memory.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "scope": row.scope,
            "memory_type": row.memory_type,
            "content": row.content,
            "confidence": row.confidence,
        }
        for row in rows
    ]
