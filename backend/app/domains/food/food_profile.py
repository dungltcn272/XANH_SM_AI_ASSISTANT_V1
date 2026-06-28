from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Memory


def get_food_profile(db: Session | None, actor_id: str | None) -> dict:
    if db is None or not actor_id:
        return {"actor_id": actor_id, "diet": [], "budget_vnd": None, "favorite_cuisines": []}
    rows = (
        db.query(Memory)
        .filter(Memory.actor_id == actor_id, Memory.status == "active", Memory.scope.in_(["food", "general"]))
        .order_by(Memory.updated_at.desc())
        .limit(30)
        .all()
    )
    preferences = [row.content for row in rows if row.memory_type in {"preference", "constraint", "location"}]
    return {"actor_id": actor_id, "preferences": preferences, "budget_vnd": None, "favorite_cuisines": []}
