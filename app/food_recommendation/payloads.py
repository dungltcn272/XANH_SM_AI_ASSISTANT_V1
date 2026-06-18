from __future__ import annotations

from typing import Any


def format_vnd(value: int | None) -> str:
    if value is None:
        return "Đang cập nhật"
    return f"{int(value):,}đ".replace(",", ".")


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
        return "Đang cập nhật"
    if distance_km < 1:
        return f"{int(round(distance_km * 1000))} m"
    return f"{distance_km:.1f} km"


def missing_location_answer() -> str:
    return (
        "Dạ, em cần vị trí giao món để sắp xếp các quán gần anh/chị chính xác hơn. "
        "Anh/chị có thể dùng vị trí hiện tại hoặc nhập địa chỉ giao hàng bên dưới."
    )


def format_food_answer(items: list[Any], category: str | None = None) -> str:
    if not items:
        return (
            "Dạ, em chưa tìm được quán phù hợp quanh vị trí này trong catalog hiện tại. "
            "Anh/chị có thể chọn lại vị trí ở khu vực trung tâm hoặc nhập địa chỉ cụ thể hơn để em tìm chính xác."
        )

    intro = "Dạ, em đã sắp xếp một vài lựa chọn"
    if category:
        intro += f" cho món {category}"
    return intro + " gần anh/chị. Em ưu tiên khoảng cách, thời gian giao và mức độ phù hợp với nhu cầu."


def food_location_payload(query: str) -> dict[str, Any]:
    return {
        "title": "Bạn muốn giao đến đâu?",
        "query": query,
        "address_placeholder": "Nhập địa chỉ giao hàng",
        "current_location_label": "Dùng vị trí hiện tại",
        "submit_label": "Tìm quán gần đây",
    }


def food_recommendations_payload(
    items: list[Any],
    category: str | None = None,
    query: str | None = None,
    answer_meta: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    title = "Một vài quán phù hợp gần bạn"
    if category:
        title = f"Một vài quán {category} phù hợp gần bạn"

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
            "eta_text": f"{item.eta_minutes} phút" if item.eta_minutes else "Đang cập nhật",
            "delivery_fee": item.delivery_fee,
            "delivery_fee_text": format_vnd(item.delivery_fee),
            "price": price,
            "price_text": format_vnd(price) if price else "",
            "reason": item.reason,
            "score": item.score,
            "score_breakdown": item.score_breakdown.model_dump() if hasattr(item.score_breakdown, 'model_dump') else item.score_breakdown.dict() if hasattr(item.score_breakdown, 'dict') else vars(item.score_breakdown) if hasattr(item.score_breakdown, '__dict__') else item.score_breakdown,
            "is_best": index == 0,
        }

    return {
        "title": (answer_meta or {}).get("cards_title") or title,
        "subtitle": (answer_meta or {}).get("cards_subtitle")
        or "Đã sắp xếp theo khoảng cách, thời gian giao hàng và mức độ phù hợp với nhu cầu của bạn.",
        "query": query,
        "trace_id": trace_id,
        "items": [to_payload(item, index) for index, item in enumerate(items[:4])],
        "more_items": [to_payload(item, index + 4) for index, item in enumerate(items[4:8])],
    }

