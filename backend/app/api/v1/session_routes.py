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
from app.integrations.google_client import verify_google_credential


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
    if not settings.GOOGLE_CLIENT_ID or settings.GOOGLE_CLIENT_ID == "your-google-client-id-here":
        raise HTTPException(status_code=503, detail="GOOGLE_CLIENT_ID is not configured")
    profile = verify_google_credential(req.token)
    if profile is None:
        raise HTTPException(status_code=401, detail="Google token verification failed")

    identity = db.query(ActorIdentity).filter(ActorIdentity.provider == "google", ActorIdentity.provider_subject == profile["sub"]).first()
    if identity:
        actor = db.query(Actor).filter(Actor.id == identity.actor_id).first()
    else:
        actor = db.query(Actor).filter(Actor.email == profile.get("email")).first() if profile.get("email") else None
        if not actor:
            actor = Actor(actor_type="customer", display_name=profile.get("name"), email=profile.get("email"), status="active")
            db.add(actor)
            db.flush()
        _create_identity(db, actor=actor, provider="google", subject=profile["sub"], metadata=profile)
    if not actor:
        raise HTTPException(status_code=401, detail="Google actor could not be resolved")
    actor.display_name = profile.get("name") or actor.display_name
    if profile.get("email") and not actor.email:
        actor.email = profile["email"]
    db.commit()
    db.refresh(actor)
    return {
        "access_token": create_access_token({"sub": actor.id, "type": "user"}),
        "token_type": "bearer",
        "user_id": actor.id,
        "email": actor.email,
        "name": actor.name,
        "avatar_url": profile.get("picture"),
        "role": actor.role.value,
        "type": "user",
    }


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
