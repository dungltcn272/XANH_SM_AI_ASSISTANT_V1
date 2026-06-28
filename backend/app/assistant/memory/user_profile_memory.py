from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import ProfileSnapshot


def get_profile_snapshot(db: Session, *, actor_id: str | None, persona_id: str) -> dict[str, Any]:
    if not actor_id:
        return {}
    row = (
        db.query(ProfileSnapshot)
        .filter(ProfileSnapshot.actor_id == actor_id)
        .filter((ProfileSnapshot.persona_id == persona_id) | (ProfileSnapshot.persona_id.is_(None)))
        .order_by(ProfileSnapshot.updated_at.desc())
        .first()
    )
    if not row or not row.profile_json:
        return {}
    try:
        return json.loads(row.profile_json)
    except json.JSONDecodeError:
        return {}
