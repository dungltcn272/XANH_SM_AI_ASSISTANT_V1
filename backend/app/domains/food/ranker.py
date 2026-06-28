from __future__ import annotations

import math

from app.config.settings import settings
from app.domains.food.schemas import FoodCandidate, FoodSearchContext


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _normalize_rating(value: float | None) -> float:
    if value is None:
        return 0.5
    if value > 5:
        return min(1.0, value / 1000)
    return min(1.0, max(0.0, value / 5))


def rank_food_candidates(
    candidates: list[FoodCandidate],
    *,
    context: FoodSearchContext | None = None,
    limit: int = 8,
) -> list[FoodCandidate]:
    context = context or FoodSearchContext()
    radius = context.radius_km or settings.FOOD_SEARCH_RADIUS_KM
    ranked = []
    max_keyword = max([item.score_breakdown.get("keyword_score", 0.0) for item in candidates] or [1.0]) or 1.0

    for item in candidates:
        distance_score = 0.5
        if context.lat is not None and context.lng is not None and item.merchant_lat is not None and item.merchant_lng is not None:
            distance = haversine_km(context.lat, context.lng, item.merchant_lat, item.merchant_lng)
            item.distance_km = round(distance, 2)
            item.eta_minutes = round(12 + distance * 4, 1)
            if distance > radius:
                continue
            distance_score = max(0.0, 1 - distance / radius)

        keyword_score = float(item.score_breakdown.get("keyword_score", 0.0)) / max_keyword
        rating_score = _normalize_rating(item.merchant_rating)
        review_score = min(1.0, math.log10((item.merchant_review_count or 0) + 1) / 3)
        price_score = 0.5
        price = item.final_price or item.price
        if context.budget_vnd and price:
            price_score = 1.0 if price <= context.budget_vnd else max(0.0, 1 - (price - context.budget_vnd) / context.budget_vnd)

        item.score_breakdown.update(
            {
                "keyword_score_norm": round(keyword_score, 4),
                "distance_score": round(distance_score, 4),
                "rating_score": round(rating_score, 4),
                "review_score": round(review_score, 4),
                "price_score": round(price_score, 4),
            }
        )
        item.score = round(0.38 * keyword_score + 0.24 * distance_score + 0.18 * rating_score + 0.12 * review_score + 0.08 * price_score, 4)
        ranked.append(item)

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:limit]
