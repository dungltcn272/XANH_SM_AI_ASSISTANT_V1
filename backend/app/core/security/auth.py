from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security.jwt import decode_access_token, oauth2_scheme
from app.db.session import get_db
from app.db.models import Actor, ActorIdentity


def get_current_entity(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> dict:
    if not token:
        return {"type": "anonymous", "entity": None}

    try:
        payload = decode_access_token(token)
        entity_type = payload.get("type")
        entity_id = payload.get("sub")

        if entity_type == "user":
            actor = db.query(Actor).filter(Actor.id == entity_id).first()
            if actor:
                return {"type": "user", "entity": actor}

        if entity_type == "guest":
            identity = (
                db.query(ActorIdentity)
                .filter(
                    ActorIdentity.provider == "guest",
                    ActorIdentity.provider_subject == entity_id,
                )
                .first()
            )
            if identity:
                actor = db.query(Actor).filter(Actor.id == identity.actor_id).first()
                if actor:
                    return {"type": "guest", "entity": actor}
    except Exception:
        pass

    return {"type": "anonymous", "entity": None}


def get_current_admin(entity: dict = Depends(get_current_entity)):
    actor = entity.get("entity")
    if entity.get("type") != "user" or not actor or actor.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return actor
