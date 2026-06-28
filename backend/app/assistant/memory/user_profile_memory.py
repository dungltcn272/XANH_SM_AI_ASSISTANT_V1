from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Memory, ProfileSnapshot


def refresh_profile_snapshot(db: Session, *, actor_id: str | None, persona_id: str) -> dict[str, Any]:
    if not actor_id:
        return {}
    rows = (
        db.query(Memory)
        .filter(Memory.actor_id == actor_id, Memory.status == "active")
        .filter((Memory.persona_id == persona_id) | (Memory.persona_id.is_(None)))
        .order_by(Memory.updated_at.desc())
        .limit(100)
        .all()
    )
    profile: dict[str, Any] = {
        "actor_id": actor_id,
        "persona_id": persona_id,
        "facts": [],
        "preferences": [],
        "constraints": [],
        "locations": [],
        "food": {"preferences": [], "dislikes": [], "constraints": [], "locations": []},
        "source_count": len(rows),
    }
    source_ids: list[str] = []
    for row in rows:
        source_ids.append(row.id)
        item = {
            "id": row.id,
            "scope": row.scope,
            "memory_type": row.memory_type,
            "content": row.content,
            "confidence": row.confidence,
        }
        if row.memory_type == "fact":
            profile["facts"].append(item)
        elif row.memory_type in {"preference", "like"}:
            profile["preferences"].append(item)
        elif row.memory_type in {"constraint", "dislike"}:
            profile["constraints"].append(item)
        elif row.memory_type == "location":
            profile["locations"].append(item)
        if row.scope == "food":
            if row.memory_type in {"preference", "like"}:
                profile["food"]["preferences"].append(item)
            elif row.memory_type == "dislike":
                profile["food"]["dislikes"].append(item)
            elif row.memory_type == "constraint":
                profile["food"]["constraints"].append(item)
            elif row.memory_type == "location":
                profile["food"]["locations"].append(item)

    row = (
        db.query(ProfileSnapshot)
        .filter(ProfileSnapshot.actor_id == actor_id, ProfileSnapshot.persona_id == persona_id)
        .order_by(ProfileSnapshot.updated_at.desc())
        .first()
    )
    if row:
        row.profile_json = json.dumps(profile, ensure_ascii=False, default=str)
        row.source_memory_ids_json = json.dumps(source_ids, ensure_ascii=False)
    else:
        db.add(
            ProfileSnapshot(
                actor_id=actor_id,
                persona_id=persona_id,
                profile_json=json.dumps(profile, ensure_ascii=False, default=str),
                source_memory_ids_json=json.dumps(source_ids, ensure_ascii=False),
            )
        )
    db.commit()
    return profile


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
