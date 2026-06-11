from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import UserReview, Message
from app.core.security import get_current_entity

router = APIRouter()

class CreateReviewRequest(BaseModel):
    conversation_id: Optional[str] = None
    message_id: str
    rating: str # 'up' or 'down'
    reason_tags: Optional[List[str]] = None
    comment: Optional[str] = None

@router.post("")
def submit_review(req: CreateReviewRequest, db: Session = Depends(get_db), entity: dict = Depends(get_current_entity)):
    # Validate rating
    if req.rating not in ["up", "down"]:
        raise HTTPException(status_code=400, detail="Rating must be 'up' or 'down'")
        
    # Check if a review already exists for this message
    existing_review = db.query(UserReview).filter(UserReview.message_id == req.message_id).first()
    
    # Try to find the message to extract query, answer, and trace
    message = db.query(Message).filter(Message.id == req.message_id).first()
    query_text = None
    answer_text = None
    pipeline_trace = None
    
    if message:
        answer_text = message.content
        pipeline_trace = message.pipeline_trace
        # Find the preceding message (the user's query)
        prev_msg = db.query(Message).filter(
            Message.conversation_id == message.conversation_id,
            Message.created_at < message.created_at,
            Message.role == "user"
        ).order_by(Message.created_at.desc()).first()
        if prev_msg:
            query_text = prev_msg.content
            
    import json
    reason_tags_json = json.dumps(req.reason_tags, ensure_ascii=False) if req.reason_tags else None
    
    user_id = entity.get("entity").id if entity.get("type") in ["user", "guest"] and entity.get("entity") else None
    
    if existing_review:
        # Update existing review
        existing_review.rating = req.rating
        existing_review.reason_tags = reason_tags_json
        existing_review.comment = req.comment
        db.commit()
        db.refresh(existing_review)
        return {"success": True, "action": "updated", "review_id": existing_review.id}
    else:
        # Create new review
        new_review = UserReview(
            message_id=req.message_id,
            rating=req.rating,
            reason_tags=reason_tags_json,
            comment=req.comment,
            status="new"
        )
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
        return {"success": True, "action": "created", "review_id": new_review.id}
