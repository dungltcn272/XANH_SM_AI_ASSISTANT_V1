from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.assistant.memory.long_term_memory import list_actor_memories, supersede_memory, update_memory_status
from app.assistant.memory.user_profile_memory import refresh_profile_snapshot
from app.core.dependency import get_current_entity, get_db


router = APIRouter()


class MemoryUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1)


def _actor_id(current_entity: dict) -> str:
    actor = current_entity.get("entity")
    actor_id = getattr(actor, "id", None)
    if not actor_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return actor_id


def _memory_payload(row) -> dict:
    return {
        "id": row.id,
        "persona_id": row.persona_id,
        "memory_type": row.memory_type,
        "scope": row.scope,
        "content": row.content,
        "confidence": row.confidence,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


@router.get("")
def list_memories(
    persona_id: str | None = None,
    status: str = "active",
    limit: int = 50,
    db: Session = Depends(get_db),
    current_entity: dict = Depends(get_current_entity),
) -> list[dict]:
    actor_id = _actor_id(current_entity)
    rows = list_actor_memories(db, actor_id=actor_id, persona_id=persona_id, status=status, limit=max(1, min(limit, 200)))
    return [_memory_payload(row) for row in rows]


@router.post("/{memory_id}/forget")
def forget_memory(memory_id: str, db: Session = Depends(get_db), current_entity: dict = Depends(get_current_entity)) -> dict:
    actor_id = _actor_id(current_entity)
    row = update_memory_status(db, actor_id=actor_id, memory_id=memory_id, status="deleted")
    if not row:
        raise HTTPException(status_code=404, detail="Memory not found")
    if row.persona_id:
        refresh_profile_snapshot(db, actor_id=actor_id, persona_id=row.persona_id)
    return {"status": "deleted", "memory_id": memory_id}


@router.post("/{memory_id}/expire")
def expire_memory(memory_id: str, db: Session = Depends(get_db), current_entity: dict = Depends(get_current_entity)) -> dict:
    actor_id = _actor_id(current_entity)
    row = update_memory_status(db, actor_id=actor_id, memory_id=memory_id, status="expired")
    if not row:
        raise HTTPException(status_code=404, detail="Memory not found")
    if row.persona_id:
        refresh_profile_snapshot(db, actor_id=actor_id, persona_id=row.persona_id)
    return {"status": "expired", "memory_id": memory_id}


@router.put("/{memory_id}")
def edit_memory(memory_id: str, req: MemoryUpdateRequest, db: Session = Depends(get_db), current_entity: dict = Depends(get_current_entity)) -> dict:
    actor_id = _actor_id(current_entity)
    row = supersede_memory(db, actor_id=actor_id, memory_id=memory_id, new_content=req.content)
    if not row:
        raise HTTPException(status_code=404, detail="Memory not found")
    if row.persona_id:
        refresh_profile_snapshot(db, actor_id=actor_id, persona_id=row.persona_id)
    return {"status": "superseded", "memory": _memory_payload(row)}
