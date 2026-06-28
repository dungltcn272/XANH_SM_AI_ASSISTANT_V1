from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Message


def _to_langchain_message(row: Message):
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    if row.role == "user":
        return HumanMessage(content=row.content or "")
    if row.role == "assistant":
        return AIMessage(content=row.content or "")
    return SystemMessage(content=row.content or "")


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


def get_recent_langchain_messages(db: Session, conversation_id: str | None, limit: int = 12) -> list:
    if not conversation_id:
        return []
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_to_langchain_message(row) for row in reversed(rows)]


def get_langchain_chat_history(db: Session, conversation_id: str | None, limit: int = 12):
    from langchain_core.chat_history import InMemoryChatMessageHistory

    history = InMemoryChatMessageHistory()
    history.add_messages(get_recent_langchain_messages(db, conversation_id, limit=limit))
    return history
