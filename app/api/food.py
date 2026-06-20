import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.security import get_current_entity
from app.db.database import get_db
from app.db.models import FoodCatalog, FoodInteraction
from app.food_recommendation.location.geocode import geocode_address
from app.food_recommendation.profile.profile_store import get_or_create_food_profile, save_food_location

router = APIRouter()

VALID_FOOD_EVENTS = {"impression", "click_item", "click_out", "like", "dismiss", "dislike"}


class FoodInteractionRequest(BaseModel):
    event_type: str
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    item_id: Optional[str] = None
    merchant_id: Optional[str] = None
    rank_position: Optional[int] = None
    query: Optional[str] = None
    request_context: Optional[Dict[str, Any]] = None


class FoodLocationRequest(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = None
    label: Optional[str] = None
    address: Optional[str] = None
    lat: float
    lng: float
    source: Optional[str] = "user"
    saved_at: Optional[str] = None
    set_current: bool = True


def _append_unique(items: list[dict[str, Any]], value: dict[str, Any], key: str = "item_id", limit: int = 80) -> list[dict[str, Any]]:
    value_key = value.get(key)
    filtered = [item for item in items if item.get(key) != value_key] if value_key else items
    return [value, *filtered][:limit]


def _update_food_profile_from_event(
    db: Session,
    user_id: str | None,
    session_id: str | None,
    req: FoodInteractionRequest,
) -> None:
    if req.event_type not in {"like", "dismiss", "dislike", "click_item", "click_out"}:
        return

    profile = get_or_create_food_profile(db, user_id=user_id, guest_id=session_id)
    context = req.request_context or {}
    snapshot = {
        "item_id": req.item_id,
        "merchant_id": req.merchant_id,
        "name": context.get("item_name"),
        "dish_name": context.get("dish_name"),
        "category": context.get("category"),
        "tags": context.get("tags") or [],
        "event_type": req.event_type,
    }

    try:
        liked = json.loads(profile.liked_items_json or "[]")
    except json.JSONDecodeError:
        liked = []
    try:
        disliked = json.loads(profile.disliked_items_json or "[]")
    except json.JSONDecodeError:
        disliked = []

    if req.event_type in {"like", "click_item", "click_out"}:
        profile.liked_items_json = json.dumps(_append_unique(liked, snapshot), ensure_ascii=False)
    elif req.event_type in {"dismiss", "dislike"}:
        profile.disliked_items_json = json.dumps(_append_unique(disliked, snapshot), ensure_ascii=False)


@router.get("/geocode")
def geocode_food_address(address: str = Query(..., min_length=3, max_length=240)):
    try:
        result = geocode_address(address)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Geocode provider unavailable: {exc}") from exc
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy vị trí phù hợp cho địa chỉ này")
    return result


@router.post("/interactions")
def log_food_interaction(
    req: FoodInteractionRequest,
    db: Session = Depends(get_db),
    entity: dict = Depends(get_current_entity),
):
    if req.event_type not in VALID_FOOD_EVENTS:
        raise HTTPException(status_code=400, detail="Unsupported food interaction event_type")

    entity_type = entity.get("type")
    entity_obj = entity.get("entity")
    user_id = entity_obj.id if entity_type == "user" and entity_obj else None
    session_id = entity_obj.id if entity_type == "guest" and entity_obj else None

    row = FoodInteraction(
        user_id=user_id,
        session_id=session_id,
        conversation_id=req.conversation_id,
        message_id=req.message_id,
        event_type=req.event_type,
        item_id=req.item_id,
        merchant_id=req.merchant_id,
        rank_position=req.rank_position,
        query=req.query,
        request_context_json=json.dumps(req.request_context or {}, ensure_ascii=False),
    )
    db.add(row)
    _update_food_profile_from_event(db, user_id, session_id, req)
    db.commit()
    db.refresh(row)
    return {"success": True, "event_id": row.event_id}


@router.post("/locations")
def save_location(
    req: FoodLocationRequest,
    db: Session = Depends(get_db),
    entity: dict = Depends(get_current_entity),
):
    if not (8 <= float(req.lat) <= 24 and 102 <= float(req.lng) <= 110):
        raise HTTPException(status_code=400, detail="Location is outside supported Vietnam bounds")

    entity_type = entity.get("type")
    entity_obj = entity.get("entity")
    user_id = entity_obj.id if entity_type == "user" and entity_obj else None
    session_id = entity_obj.id if entity_type == "guest" and entity_obj else None
    location = save_food_location(
        db,
        user_id=user_id,
        guest_id=session_id,
        location=req.model_dump(),
        set_current=req.set_current,
    )
    return {"success": True, "location": location}


@router.get("/interactions/stats")
def food_interaction_stats(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    event_counts = (
        db.query(FoodInteraction.event_type, func.count(FoodInteraction.event_id))
        .group_by(FoodInteraction.event_type)
        .all()
    )
    top_items = (
        db.query(
            FoodInteraction.item_id,
            FoodCatalog.name,
            FoodCatalog.merchant_name,
            func.count(FoodInteraction.event_id).label("events"),
            func.sum(case((FoodInteraction.event_type == "click_out", 1), else_=0)).label("click_outs"),
        )
        .outerjoin(FoodCatalog, FoodCatalog.item_id == FoodInteraction.item_id)
        .filter(FoodInteraction.item_id.isnot(None))
        .group_by(FoodInteraction.item_id, FoodCatalog.name, FoodCatalog.merchant_name)
        .order_by(func.count(FoodInteraction.event_id).desc())
        .limit(limit)
        .all()
    )
    recent_events = (
        db.query(FoodInteraction)
        .order_by(FoodInteraction.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "event_counts": {event_type: count for event_type, count in event_counts},
        "top_items": [
            {
                "item_id": item_id,
                "name": name,
                "merchant_name": merchant_name,
                "events": int(events or 0),
                "click_outs": int(click_outs or 0),
            }
            for item_id, name, merchant_name, events, click_outs in top_items
        ],
        "recent_events": [
            {
                "event_id": row.event_id,
                "event_type": row.event_type,
                "item_id": row.item_id,
                "rank_position": row.rank_position,
                "conversation_id": row.conversation_id,
                "message_id": row.message_id,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in recent_events
        ],
    }
