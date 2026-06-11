from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import Optional, List
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import UserReview, Message

router = APIRouter()

class UpdateReviewStatusRequest(BaseModel):
    status: str # 'new', 'reviewed', 'promoted', 'rejected'
    admin_note: Optional[str] = None

@router.get("")
def list_reviews(
    status: Optional[str] = None,
    rating: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(UserReview).outerjoin(Message, UserReview.message_id == Message.id)
    
    if status:
        query = query.filter(UserReview.status == status)
    if rating:
        query = query.filter(UserReview.rating == rating)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Message.content.ilike(pattern),
                UserReview.comment.ilike(pattern),
                UserReview.reason_tags.ilike(pattern)
            )
        )
        
    total = query.count()
    rows = query.order_by(desc(UserReview.created_at)).offset(offset).limit(limit).all()
    
    import json
    data = []
    for row in rows:
        message = db.query(Message).filter(Message.id == row.message_id).first()
        answer = message.content if message else None
        conversation_id = message.conversation_id if message else None
        
        query_text = None
        if message:
            prev_msg = db.query(Message).filter(
                Message.conversation_id == message.conversation_id,
                Message.created_at < message.created_at,
                Message.role == "user"
            ).order_by(Message.created_at.desc()).first()
            if prev_msg:
                query_text = prev_msg.content

        row_dict = {
            "id": row.id,
            "conversation_id": conversation_id,
            "message_id": row.message_id,
            "user_id": None,
            "query": query_text,
            "answer": answer,
            "rating": row.rating,
            "reason_tags": json.loads(row.reason_tags) if row.reason_tags else [],
            "comment": row.comment,
            "status": row.status,
            "admin_note": row.admin_note,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": None,
        }
        data.append(row_dict)
        
    return {
        "total": total,
        "data": data
    }

@router.get("/{review_id}")
def get_review_detail(review_id: str, db: Session = Depends(get_db)):
    row = db.query(UserReview).filter(UserReview.id == review_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Review not found")
        
    message = db.query(Message).filter(Message.id == row.message_id).first()
    answer = message.content if message else None
    conversation_id = message.conversation_id if message else None
    pipeline_trace = message.pipeline_trace if message else None
    
    query_text = None
    if message:
        prev_msg = db.query(Message).filter(
            Message.conversation_id == message.conversation_id,
            Message.created_at < message.created_at,
            Message.role == "user"
        ).order_by(Message.created_at.desc()).first()
        if prev_msg:
            query_text = prev_msg.content

    import json
    return {
        "id": row.id,
        "conversation_id": conversation_id,
        "message_id": row.message_id,
        "user_id": None,
        "query": query_text,
        "answer": answer,
        "rating": row.rating,
        "reason_tags": json.loads(row.reason_tags) if row.reason_tags else [],
        "comment": row.comment,
        "pipeline_trace": json.loads(pipeline_trace) if pipeline_trace else None,
        "status": row.status,
        "admin_note": row.admin_note,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": None,
    }

@router.put("/{review_id}")
def update_review_status(review_id: str, req: UpdateReviewStatusRequest, db: Session = Depends(get_db)):
    row = db.query(UserReview).filter(UserReview.id == review_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Review not found")
        
    valid_statuses = ["new", "reviewed", "promoted", "rejected"]
    if req.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
    row.status = req.status
    if req.admin_note is not None:
        row.admin_note = req.admin_note
        
    db.commit()
    db.refresh(row)
    
    return {"success": True, "status": row.status, "admin_note": row.admin_note}
