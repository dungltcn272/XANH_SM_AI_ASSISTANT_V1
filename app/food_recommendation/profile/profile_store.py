from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import ProfileSnapshot as UserFoodProfile


def _json_or_default(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _append_unique_place(items: list[dict[str, Any]] | None, value: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
    items_list = items if items is not None else []
    place_id = value.get("id")
    label = str(value.get("label") or "").casefold()
    filtered = [
        item for item in items_list
        if item.get("id") != place_id and str(item.get("label") or "").casefold() != label
    ]
    return [value, *filtered][:limit]


def _profile_identity(user_id: str | None = None, guest_id: str | None = None) -> dict[str, str | None]:
    normalized_user_id = user_id if user_id and user_id != "anonymous" else None
    normalized_guest_id = guest_id if guest_id and guest_id != "anonymous" else None
    return {
        "user_id": normalized_user_id,
        "guest_id": normalized_guest_id,
        "actor_id": normalized_user_id or normalized_guest_id,
    }


def get_or_create_food_profile(
    db: Session,
    user_id: str | None = None,
    guest_id: str | None = None,
) -> UserFoodProfile:
    identity = _profile_identity(user_id, guest_id)
    query = db.query(UserFoodProfile)
    if identity["actor_id"]:
        row = query.filter(UserFoodProfile.actor_id == identity["actor_id"]).first()
    else:
        row = None

    if row:
        return row
    if not identity["actor_id"]:
        return UserFoodProfile(actor_id="anonymous", profile_json=json.dumps({}, ensure_ascii=False))

    row = UserFoodProfile(actor_id=identity["actor_id"], profile_json=json.dumps({}, ensure_ascii=False))
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


def save_food_location(
    db: Session,
    *,
    user_id: str | None = None,
    guest_id: str | None = None,
    location: dict[str, Any],
    set_current: bool = True,
) -> dict[str, Any]:
    row = get_or_create_food_profile(db, user_id=user_id, guest_id=guest_id)
    saved_places = _json_or_default(row.saved_places_json, [])
    clean_location = {
        "id": location.get("id") or location.get("type") or location.get("label") or "current",
        "type": location.get("type") or location.get("id"),
        "label": location.get("label") or location.get("address") or "Vị trí đã lưu",
        "address": location.get("address") or location.get("label"),
        "lat": float(location.get("lat")),
        "lng": float(location.get("lng")),
        "source": location.get("source") or "user",
        "saved_at": location.get("saved_at"),
    }
    row.saved_places_json = json.dumps(_append_unique_place(saved_places, clean_location), ensure_ascii=False)
    if set_current:
        row.current_location_json = json.dumps(clean_location, ensure_ascii=False)
    db.commit()
    db.refresh(row)
    return clean_location


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
