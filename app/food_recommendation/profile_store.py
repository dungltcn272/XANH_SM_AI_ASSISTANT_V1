from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import UserFoodProfile


def _json_or_default(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _profile_identity(user_id: str | None = None, guest_id: str | None = None) -> dict[str, str | None]:
    return {
        "user_id": user_id if user_id and user_id != "anonymous" else None,
        "guest_id": guest_id if guest_id and guest_id != "anonymous" else None,
    }


def get_or_create_food_profile(
    db: Session,
    user_id: str | None = None,
    guest_id: str | None = None,
) -> UserFoodProfile:
    identity = _profile_identity(user_id, guest_id)
    query = db.query(UserFoodProfile)
    if identity["user_id"]:
        row = query.filter(UserFoodProfile.user_id == identity["user_id"]).first()
    elif identity["guest_id"]:
        row = query.filter(UserFoodProfile.guest_id == identity["guest_id"]).first()
    else:
        row = None

    if row:
        return row

    row = UserFoodProfile(user_id=identity["user_id"], guest_id=identity["guest_id"])
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def food_profile_context(
    db: Session | None = None,
    user_id: str | None = None,
    guest_id: str | None = None,
) -> dict[str, Any]:
    if db is None or (not user_id and not guest_id):
        return empty_food_context()

    row = get_or_create_food_profile(db, user_id=user_id, guest_id=guest_id)
    return {
        "current_location": _json_or_default(row.current_location_json, None),
        "saved_places": _json_or_default(row.saved_places_json, []),
        "liked_foods": _json_or_default(row.liked_items_json, []),
        "disliked_foods": _json_or_default(row.disliked_items_json, []),
        "preferred_categories": _json_or_default(row.preferred_categories_json, None),
        "preferred_tags": _json_or_default(row.preferred_tags_json, None),
        "avoided_tags": _json_or_default(row.avoided_tags_json, None),
        "budget_profile": _json_or_default(row.budget_profile_json, None),
        "allergies": _json_or_default(row.allergies_json, None),
        "profile_stats": _json_or_default(row.profile_stats_json, None),
    }


def empty_food_context() -> dict[str, Any]:
    return {
        "current_location": None,
        "saved_places": [],
        "liked_foods": [],
        "disliked_foods": [],
        "preferred_categories": None,
        "preferred_tags": None,
        "avoided_tags": None,
        "budget_profile": None,
        "allergies": None,
        "profile_stats": None,
    }
