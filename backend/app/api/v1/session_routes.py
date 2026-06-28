from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.security import create_access_token
from app.core.security.password import verify_plain_password
from app.db.models import Actor, ActorIdentity, UserRole
from app.db.session import get_db


router = APIRouter()


class GoogleAuthRequest(BaseModel):
    token: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


def _create_identity(db: Session, *, actor: Actor, provider: str, subject: str, metadata: dict | None = None) -> None:
    existing = db.query(ActorIdentity).filter(ActorIdentity.provider == provider, ActorIdentity.provider_subject == subject).first()
    if existing:
        return
    db.add(ActorIdentity(actor_id=actor.id, provider=provider, provider_subject=subject, metadata_json=json.dumps(metadata or {}, ensure_ascii=False)))


@router.post("/guest")
def create_guest_session(db: Session = Depends(get_db)) -> dict:
    session_token = str(uuid.uuid4())
    actor = Actor(actor_type="guest", display_name="Guest")
    db.add(actor)
    db.flush()
    _create_identity(db, actor=actor, provider="guest", subject=session_token, metadata={"session_token": session_token})
    db.commit()
    db.refresh(actor)
    return {"access_token": create_access_token({"sub": session_token, "type": "guest"}), "token_type": "bearer", "guest_id": actor.id, "type": "guest"}


@router.post("/google")
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=501, detail="Google auth client verification will be added in integrations/google_client.py")


@router.post("/admin-login")
def admin_login(req: AdminLoginRequest, db: Session = Depends(get_db)) -> dict:
    if req.username != settings.ADMIN_USERNAME or not verify_plain_password(req.password, settings.ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    admin_email = f"{req.username}@system.admin"
    actor = db.query(Actor).filter(Actor.email == admin_email).first()
    if not actor:
        actor = Actor(email=admin_email, display_name="System Admin", actor_type="admin")
        db.add(actor)
        db.flush()
        _create_identity(db, actor=actor, provider="admin_password", subject=req.username, metadata={"username": req.username})
    elif actor.role != UserRole.ADMIN:
        actor.role = UserRole.ADMIN
    db.commit()
    db.refresh(actor)
    return {"access_token": create_access_token({"sub": actor.id, "type": "user"}), "token_type": "bearer", "user_id": actor.id, "email": actor.email, "name": actor.name, "role": actor.role.value, "type": "user"}
