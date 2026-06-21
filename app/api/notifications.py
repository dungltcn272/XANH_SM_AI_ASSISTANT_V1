from datetime import datetime
from typing import Optional

import pytz
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_entity
from app.db.database import get_db
from app.db.models import AdminNotification, NotificationRead, NotificationStatus, User, get_vn_time


router = APIRouter()


class MarkReadResponse(BaseModel):
    ok: bool


def _serialize_notification(notification: AdminNotification, read_ids: set[str]) -> dict:
    return {
        "id": notification.id,
        "title": notification.title,
        "summary": notification.summary,
        "body": notification.body,
        "type": notification.notification_type,
        "status": notification.status.value,
        "audience": notification.audience.value,
        "priority": notification.priority,
        "action_label": notification.action_label,
        "action_url": notification.action_url,
        "published_at": notification.published_at.isoformat() if notification.published_at else None,
        "expires_at": notification.expires_at.isoformat() if notification.expires_at else None,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
        "is_read": notification.id in read_ids,
    }


def _current_user(entity: dict) -> Optional[User]:
    return entity.get("entity") if entity.get("type") == "user" else None


@router.get("")
def list_notifications(
    db: Session = Depends(get_db),
    entity: dict = Depends(get_current_entity),
):
    user = _current_user(entity)
    now = get_vn_time()
    rows = (
        db.query(AdminNotification)
        .filter(
            AdminNotification.status == NotificationStatus.PUBLISHED,
            or_(AdminNotification.published_at.is_(None), AdminNotification.published_at <= now),
            or_(AdminNotification.expires_at.is_(None), AdminNotification.expires_at > now),
        )
        .order_by(AdminNotification.priority.asc(), AdminNotification.published_at.desc().nullslast(), AdminNotification.created_at.desc())
        .limit(50)
        .all()
    )
    read_ids: set[str] = set()
    if user:
        read_ids = {
            row.notification_id
            for row in db.query(NotificationRead.notification_id).filter(NotificationRead.user_id == user.id).all()
        }
    items = [_serialize_notification(row, read_ids) for row in rows]
    return {
        "items": items,
        "unread_count": sum(1 for item in items if not item["is_read"]),
    }


@router.post("/{notification_id}/read", response_model=MarkReadResponse)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    entity: dict = Depends(get_current_entity),
):
    user = _current_user(entity)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    exists = db.query(AdminNotification.id).filter(AdminNotification.id == notification_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.add(NotificationRead(notification_id=notification_id, user_id=user.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    return {"ok": True}


@router.post("/read-all", response_model=MarkReadResponse)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    entity: dict = Depends(get_current_entity),
):
    user = _current_user(entity)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    now = get_vn_time()
    rows = (
        db.query(AdminNotification.id)
        .filter(
            AdminNotification.status == NotificationStatus.PUBLISHED,
            or_(AdminNotification.published_at.is_(None), AdminNotification.published_at <= now),
            or_(AdminNotification.expires_at.is_(None), AdminNotification.expires_at > now),
        )
        .all()
    )
    existing = {
        row.notification_id
        for row in db.query(NotificationRead.notification_id).filter(NotificationRead.user_id == user.id).all()
    }
    for row in rows:
        if row.id not in existing:
            db.add(NotificationRead(notification_id=row.id, user_id=user.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    return {"ok": True}
