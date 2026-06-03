from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Conversation, Message
from app.core.security import get_current_entity

router = APIRouter()

@router.get("")
def get_conversations(db: Session = Depends(get_db), current_entity: dict = Depends(get_current_entity)):
    entity_type = current_entity.get("type")
    entity_obj = current_entity.get("entity")
    
    if entity_type == "user":
        convs = db.query(Conversation).filter(Conversation.user_id == entity_obj.id).order_by(Conversation.created_at.desc()).all()
    else:
        convs = db.query(Conversation).filter(Conversation.guest_id == entity_obj.id).order_by(Conversation.created_at.desc()).all()
        
    return convs

@router.get("/{conversation_id}/messages")
def get_messages(conversation_id: str, db: Session = Depends(get_db), current_entity: dict = Depends(get_current_entity)):
    entity_type = current_entity.get("type")
    entity_obj = current_entity.get("entity")
    
    # Verify ownership
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    if entity_type == "user" and conv.user_id != entity_obj.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if entity_type == "guest" and conv.guest_id != entity_obj.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    return messages
