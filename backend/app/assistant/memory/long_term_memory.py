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


def list_actor_memories(db: Session, *, actor_id: str | None, persona_id: str | None = None, status: str = "active", limit: int = 50) -> list[Memory]:
    if not actor_id:
        return []
    query = db.query(Memory).filter(Memory.actor_id == actor_id, Memory.status == status)
    if persona_id:
        query = query.filter((Memory.persona_id == persona_id) | (Memory.persona_id.is_(None)))
    return query.order_by(Memory.updated_at.desc()).limit(limit).all()


def update_memory_status(db: Session, *, actor_id: str, memory_id: str, status: str) -> Memory | None:
    row = db.query(Memory).filter(Memory.id == memory_id, Memory.actor_id == actor_id).first()
    if not row:
        return None
    row.status = status
    db.commit()
    db.refresh(row)
    return row


def supersede_memory(db: Session, *, actor_id: str, memory_id: str, new_content: str) -> Memory | None:
    row = db.query(Memory).filter(Memory.id == memory_id, Memory.actor_id == actor_id).first()
    if not row:
        return None
    row.status = "superseded"
    replacement = Memory(
        actor_id=row.actor_id,
        persona_id=row.persona_id,
        conversation_id=row.conversation_id,
        message_id=row.message_id,
        memory_type=row.memory_type,
        scope=row.scope,
        content=new_content,
        source="user_edit",
        metadata_json=row.metadata_json,
        confidence=max(row.confidence or 0.0, 0.95),
        status="active",
    )
    db.add(replacement)
    db.commit()
    db.refresh(replacement)
    return replacement
