from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FoodSlots:
    is_food_intent: bool = False
    lat: float | None = None
    lng: float | None = None
    category: str | None = None
    taste_tags: list[str] = field(default_factory=list)
    negative_taste_tags: list[str] = field(default_factory=list)
    budget_min: int | None = None
    budget_max: int | None = None
    meal_time: str | None = None
    address_text: str | None = None
    max_distance_km: float = 6


def slots_from_nlu(food_slots: dict[str, Any] | None, raw_query: str | None = None) -> FoodSlots:
    if not food_slots:
        lat, lng = extract_lat_lng(raw_query or "")
        return FoodSlots(is_food_intent=True, lat=lat, lng=lng)

    lat = _float_or_none(food_slots.get("lat"))
    lng = _float_or_none(food_slots.get("lng"))
    if lat is None or lng is None:
        lat, lng = extract_lat_lng(raw_query or "")

    max_distance = _float_or_none(food_slots.get("max_distance_km")) or 6
    return FoodSlots(
        is_food_intent=True,
        lat=lat,
        lng=lng,
        category=food_slots.get("dish_or_category") or food_slots.get("category"),
        taste_tags=_ensure_string_list(food_slots.get("taste_tags")),
        negative_taste_tags=_ensure_string_list(food_slots.get("negative_taste_tags")),
        budget_min=_int_or_none(food_slots.get("budget_min")),
        budget_max=_int_or_none(food_slots.get("budget_max")),
        meal_time=food_slots.get("meal_time"),
        address_text=food_slots.get("address_text"),
        max_distance_km=max(1.0, min(float(max_distance), 25.0)),
    )


def extract_lat_lng(text: str) -> tuple[float | None, float | None]:
    patterns = [
        r"lat\s*[:=]\s*(-?\d+(?:\.\d+)?)\s*[,;\s]+(?:lng|lon|long|longitude)\s*[:=]\s*(-?\d+(?:\.\d+)?)",
        r"(-?\d{1,2}\.\d{3,})\s*[,;]\s*(-?\d{1,3}\.\d{3,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text or "", flags=re.IGNORECASE)
        if not match:
            continue
        first = float(match.group(1))
        second = float(match.group(2))
        if is_valid_vietnam_coord(first, second):
            return first, second
        if is_valid_vietnam_coord(second, first):
            return second, first
    return None, None


def is_valid_vietnam_coord(lat: float, lng: float) -> bool:
    return 8 <= lat <= 24 and 102 <= lng <= 110


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _ensure_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return []
