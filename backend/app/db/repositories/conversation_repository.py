from sqlalchemy.orm import Session

from app.db.models import Conversation


def get_conversation(db: Session, conversation_id: str) -> Conversation | None:
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()
