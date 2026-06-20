from __future__ import annotations
from typing import Any

class FoodLocationResolver:
    """Helper to resolve coordinates from user context and request query."""

    @staticmethod
    def resolve_location_from_context(slots: Any, food_context: dict[str, Any] | None, query: str) -> str | None:
        context = food_context or {}
        query_norm = (query or "").casefold()
        saved_places = context.get("saved_places") or []
        current_location = context.get("current_location")
        candidates: list[tuple[str, dict[str, Any]]] = []

        if isinstance(current_location, dict):
            candidates.append(("current_location", current_location))
        if isinstance(saved_places, list):
            for place in saved_places:
                if isinstance(place, dict):
                    label = str(place.get("label") or place.get("name") or place.get("type") or "").casefold()
                    if label and label in query_norm:
                        candidates.insert(0, ("saved_place", place))
                    else:
                        candidates.append(("saved_place", place))

        home_words = ("nhà", "nha", "home")
        if any(word in query_norm for word in home_words):
            for source, place in candidates:
                label = str(place.get("label") or place.get("name") or place.get("type") or "").casefold()
                if source == "current_location" or label in {"nhà", "nha", "home"}:
                    lat = place.get("lat") or place.get("latitude")
                    lng = place.get("lng") or place.get("lon") or place.get("longitude")
                    if lat is not None and lng is not None:
                        slots.lat = float(lat)
                        slots.lng = float(lng)
                        slots.address_text = slots.address_text or place.get("address") or place.get("label") or "Nhà"
                        return source

        if slots.lat is None or slots.lng is None:
            if isinstance(current_location, dict):
                lat = current_location.get("lat") or current_location.get("latitude")
                lng = current_location.get("lng") or current_location.get("lon") or current_location.get("longitude")
                if lat is not None and lng is not None and any(word in query_norm for word in ("gần", "gan", "quanh", "đây", "day")):
                    slots.lat = float(lat)
                    slots.lng = float(lng)
                    slots.address_text = slots.address_text or current_location.get("address") or current_location.get("label")
                    return "current_location"
        return None
