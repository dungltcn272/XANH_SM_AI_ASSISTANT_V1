from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependency import get_current_entity, get_db
from app.db.models import Conversation, Message


router = APIRouter()


def _actor_id(entity: dict) -> str | None:
    return getattr(entity.get("entity"), "id", None)


@router.get("")
def list_conversations(db: Session = Depends(get_db), current_entity: dict = Depends(get_current_entity)) -> list[dict]:
    actor_id = _actor_id(current_entity)
    query = db.query(Conversation)
    if actor_id:
        query = query.filter(Conversation.actor_id == actor_id)
    rows = query.order_by(Conversation.updated_at.desc()).limit(50).all()
    return [
        {"id": row.id, "title": row.title, "persona_id": row.persona_id, "channel": row.channel, "status": row.status, "updated_at": row.updated_at}
        for row in rows
    ]


@router.get("/{conversation_id}/messages")
def list_messages(conversation_id: str, db: Session = Depends(get_db), current_entity: dict = Depends(get_current_entity)) -> list[dict]:
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    actor_id = _actor_id(current_entity)
    if conversation.actor_id and actor_id and conversation.actor_id != actor_id:
        raise HTTPException(status_code=403, detail="Conversation access denied")
    rows = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    result = []
    for row in rows:
        metadata = {}
        if row.metadata_json:
            try:
                metadata = json.loads(row.metadata_json)
            except json.JSONDecodeError:
                metadata = {}
        result.append({"id": row.id, "role": row.role, "content": row.content, "content_type": row.content_type, "metadata": metadata, "pipeline_trace": row.metadata_json, "created_at": row.created_at})
    return result
