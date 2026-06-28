from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.db.models import Conversation, Message


def get_or_create_conversation(db: Session, *, conversation_id: str | None, actor_id: str | None, persona_id: str) -> Conversation:
    if conversation_id:
        row = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if row:
            row.persona_id = persona_id
            db.commit()
            return row

    row = Conversation(id=conversation_id, actor_id=actor_id, persona_id=persona_id) if conversation_id else Conversation(actor_id=actor_id, persona_id=persona_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def save_message(
    db: Session,
    *,
    conversation_id: str,
    role: str,
    content: str,
    content_type: str = "text",
    metadata: dict | None = None,
) -> Message:
    row = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        content_type=content_type,
        metadata_json=json.dumps(metadata, ensure_ascii=False, default=str) if metadata is not None else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
