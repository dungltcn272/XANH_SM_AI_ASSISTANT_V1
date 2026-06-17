from __future__ import annotations

from typing import Any


def format_vnd(value: int | None) -> str:
    if value is None:
        return "Dang cap nhat"
    return f"{int(value):,}d".replace(",", ".")


def display_rating(value: float | None) -> float | None:
    if value is None:
        return None
    if value > 10:
        return round(min(value / 20, 5), 1)
    if value > 5:
        return round(min(value / 2, 5), 1)
    return round(min(value, 5), 1)


def distance_text(distance_km: float | None) -> str:
    if distance_km is None:
        return "Dang cap nhat"
    if distance_km < 1:
        return f"{int(round(distance_km * 1000))} m"
    return f"{distance_km:.1f} km"


def missing_location_answer() -> str:
    return (
        "Da, em can vi tri giao mon de sap xep cac quan gan anh/chi chinh xac hon. "
        "Anh/chi co the dung vi tri hien tai hoac nhap dia chi giao hang ben duoi."
    )


def format_food_answer(items: list[Any], category: str | None = None) -> str:
    if not items:
        return (
            "Da, em chua tim duoc quan phu hop quanh vi tri nay trong catalog hien tai. "
            "Anh/chi co the chon lai vi tri o khu vuc trung tam hoac nhap dia chi cu the hon de em tim chinh xac."
        )

    intro = "Da, em da sap xep mot vai lua chon"
    if category:
        intro += f" cho mon {category}"
    return intro + " gan anh/chi. Em uu tien khoang cach, thoi gian giao va muc do phu hop voi nhu cau."


def food_location_payload(query: str) -> dict[str, Any]:
    return {
        "title": "Ban muon giao den dau?",
        "query": query,
        "address_placeholder": "Nhap dia chi giao hang",
        "current_location_label": "Dung vi tri hien tai",
        "submit_label": "Tim quan gan day",
    }


def food_recommendations_payload(
    items: list[Any],
    category: str | None = None,
    query: str | None = None,
    answer_meta: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    title = "Mot vai quan phu hop gan ban"
    if category:
        title = f"Mot vai quan {category} phu hop gan ban"

    note_by_id = {
        note.get("item_id"): note.get("advice")
        for note in (answer_meta or {}).get("item_notes", [])
        if isinstance(note, dict)
    }

    def to_payload(item: Any, index: int) -> dict[str, Any]:
        price = item.final_price or item.price
        return {
            "item_id": item.item_id,
            "name": item.merchant_name or item.name,
            "dish_name": item.name,
            "address": item.address,
            "image_url": item.image_url,
            "order_url": item.order_url,
            "rating": display_rating(item.rating),
            "review_count": item.review_count,
            "distance_km": item.distance_km,
            "distance_text": distance_text(item.distance_km),
            "eta_minutes": item.eta_minutes,
            "eta_text": f"{item.eta_minutes} phut" if item.eta_minutes else "Dang cap nhat",
            "delivery_fee": item.delivery_fee,
            "delivery_fee_text": format_vnd(item.delivery_fee),
            "price": price,
            "price_text": format_vnd(price) if price else "",
            "reason": note_by_id.get(item.item_id) or item.reason,
            "is_best": index == 0,
        }

    return {
        "title": (answer_meta or {}).get("cards_title") or title,
        "subtitle": (answer_meta or {}).get("cards_subtitle")
        or "Da sap xep theo khoang cach, thoi gian giao hang va muc do phu hop voi nhu cau cua ban.",
        "query": query,
        "trace_id": trace_id,
        "items": [to_payload(item, index) for index, item in enumerate(items[:4])],
        "more_items": [to_payload(item, index + 4) for index, item in enumerate(items[4:8])],
    }

