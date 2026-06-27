import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
import json

from app.db.database import get_db
from app.db.models import Actor, ActorIdentity, UserRole
from app.core.security import create_access_token
from app.core.config import settings

from app.core.logger import log_error

router = APIRouter()


class GoogleAuthRequest(BaseModel):
    token: str


def _create_actor_identity(
    db: Session,
    *,
    actor: Actor,
    provider: str,
    provider_subject: str,
    metadata: dict | None = None,
) -> ActorIdentity:
    identity = ActorIdentity(
        actor_id=actor.id,
        provider=provider,
        provider_subject=provider_subject,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
    )
    db.add(identity)
    return identity

@router.post("/guest")
def create_guest_session(db: Session = Depends(get_db)):
    session_token = str(uuid.uuid4())
    guest = Actor(actor_type="guest", display_name="Guest")
    db.add(guest)
    db.flush()
    _create_actor_identity(
        db,
        actor=guest,
        provider="guest",
        provider_subject=session_token,
        metadata={"session_token": session_token},
    )
    db.commit()
    db.refresh(guest)
    
    access_token = create_access_token(
        data={"sub": session_token, "type": "guest"}
    )
    return {"access_token": access_token, "token_type": "bearer", "guest_id": guest.id, "type": "guest"}

@router.post("/google")
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(
            req.token, requests.Request(), settings.GOOGLE_CLIENT_ID, clock_skew_in_seconds=10
        )
        
        email = idinfo.get("email")
        name = idinfo.get("name", "")
        picture = idinfo.get("picture")
        
        if not email:
            raise HTTPException(status_code=400, detail="Google token does not contain email")
            
        # Check if actor exists
        user = db.query(Actor).filter(Actor.email == email).first()
        if not user:
            user = Actor(email=email, display_name=name, actor_type="customer")
            db.add(user)
            db.flush()
            _create_actor_identity(
                db,
                actor=user,
                provider="google",
                provider_subject=idinfo.get("sub") or email,
                metadata={"email": email, "picture": picture},
            )
            db.commit()
            db.refresh(user)
            
        # Create access token for our app
        access_token = create_access_token(
            data={"sub": user.id, "type": "user"}
        )
        
        return {
            "access_token": access_token, 
            "token_type": "bearer", 
            "user_id": user.id, 
            "email": user.email, 
            "name": user.name,
            "avatar_url": picture,
            "role": user.role.value,
            "type": "user"
        }
        
    except ValueError as e:
        log_error("AUTH", f"Token verification failed: {e}", error_type="ValueError")
        raise HTTPException(status_code=401, detail="Invalid Google token")

class AdminLoginRequest(BaseModel):
    username: str
    password: str

@router.post("/admin-login")
def admin_login(req: AdminLoginRequest, db: Session = Depends(get_db)):
    if req.username != settings.ADMIN_USERNAME or req.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
    admin_email = f"{req.username}@system.admin"
    user = db.query(Actor).filter(Actor.email == admin_email).first()
    if not user:
        user = Actor(email=admin_email, display_name="System Admin", actor_type="admin")
        db.add(user)
        db.flush()
        _create_actor_identity(
            db,
            actor=user,
            provider="admin_password",
            provider_subject=req.username,
            metadata={"username": req.username},
        )
        db.commit()
        db.refresh(user)
    elif user.role != UserRole.ADMIN:
        user.role = UserRole.ADMIN
        db.commit()
        
    access_token = create_access_token(
        data={"sub": user.id, "type": "user"}
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user_id": user.id, 
        "email": user.email, 
        "name": user.name,
        "role": user.role.value,
        "type": "user"
    }
