from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.admin.utils import parse_optional_datetime
from app.core.security import get_current_admin
from app.db.database import get_db
from app.db.models import AdminNotification, NotificationAudience, NotificationStatus, get_vn_time


router = APIRouter()


class AdminNotificationPayload(BaseModel):
    title: str
    summary: Optional[str] = None
    body: str
    notification_type: str = "announcement"
    audience: str = "all_users"
    priority: int = 100
    action_label: Optional[str] = None
    action_url: Optional[str] = None
    published_at: Optional[str] = None
    expires_at: Optional[str] = None


class AdminNotificationStatusPayload(BaseModel):
    status: str


def _status(value: str | None) -> NotificationStatus:
    raw = (value or "").strip().lower()
    for status in NotificationStatus:
        if raw == status.value:
            return status
    raise HTTPException(status_code=400, detail="Invalid notification status")


def _audience(value: str | None) -> NotificationAudience:
    raw = (value or NotificationAudience.ALL_USERS.value).strip().lower()
    for audience in NotificationAudience:
        if raw == audience.value:
            return audience
    raise HTTPException(status_code=400, detail="Invalid notification audience")


def _serialize(row: AdminNotification) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "summary": row.summary,
        "body": row.body,
        "notification_type": row.notification_type,
        "status": row.status.value,
        "audience": row.audience.value,
        "priority": row.priority,
        "action_label": row.action_label,
        "action_url": row.action_url,
        "published_at": row.published_at.isoformat() if row.published_at else None,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "created_by_admin_id": row.created_by_admin_id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _apply_payload(row: AdminNotification, payload: AdminNotificationPayload) -> None:
    title = payload.title.strip()
    body = payload.body.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    if not body:
        raise HTTPException(status_code=400, detail="Body is required")
    row.title = title
    row.summary = payload.summary.strip() if payload.summary else None
    row.body = body
    row.notification_type = (payload.notification_type or "announcement").strip().lower()
    row.audience = _audience(payload.audience)
    row.priority = max(0, int(payload.priority or 100))
    row.action_label = payload.action_label.strip() if payload.action_label else None
    row.action_url = payload.action_url.strip() if payload.action_url else None
    row.published_at = parse_optional_datetime(payload.published_at)
    row.expires_at = parse_optional_datetime(payload.expires_at)


@router.get("")
def list_admin_notifications(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(AdminNotification)
    if status and status != "all":
        query = query.filter(AdminNotification.status == _status(status))
    rows = query.order_by(AdminNotification.created_at.desc()).limit(100).all()
    return [_serialize(row) for row in rows]


@router.post("")
def create_admin_notification(
    payload: AdminNotificationPayload,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    row = AdminNotification(created_by_admin_id=admin.id, status=NotificationStatus.DRAFT)
    _apply_payload(row, payload)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.put("/{notification_id}")
def update_admin_notification(
    notification_id: str,
    payload: AdminNotificationPayload,
    db: Session = Depends(get_db),
):
    row = db.query(AdminNotification).filter(AdminNotification.id == notification_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    _apply_payload(row, payload)
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.post("/{notification_id}/status")
def update_admin_notification_status(
    notification_id: str,
    payload: AdminNotificationStatusPayload,
    db: Session = Depends(get_db),
):
    row = db.query(AdminNotification).filter(AdminNotification.id == notification_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    new_status = _status(payload.status)
    row.status = new_status
    if new_status == NotificationStatus.PUBLISHED and not row.published_at:
        row.published_at = get_vn_time()
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.delete("/{notification_id}")
def archive_admin_notification(
    notification_id: str,
    db: Session = Depends(get_db),
):
    row = db.query(AdminNotification).filter(AdminNotification.id == notification_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    row.status = NotificationStatus.ARCHIVED
    db.commit()
    return {"ok": True}
