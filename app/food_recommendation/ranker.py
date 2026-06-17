from __future__ import annotations

import math

from app.food_recommendation.profile import normalize_text
from app.food_recommendation.schemas import (
    FoodCatalogEntry,
    FoodRecommendation,
    FoodRecommendationRequest,
    ScoreBreakdown,
)


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def estimate_delivery_fee(item: FoodCatalogEntry, distance_km: float) -> int:
    if item.base_delivery_fee is not None:
        return int(item.base_delivery_fee + (item.fee_per_km or 0) * distance_km)
    return int(12000 + 3000 * distance_km)


def estimate_eta(item: FoodCatalogEntry, distance_km: float) -> int:
    if item.avg_prep_minutes is not None:
        return int(item.avg_prep_minutes + 4 * distance_km)
    return int(15 + 4 * distance_km)


def normalized_rating(value: float | None) -> float:
    if value is None:
        return 0.55
    if value > 10:
        return clamp(value / 100)
    if value > 5:
        return clamp(value / 10)
    return clamp(value / 5)


def match_score(needle: str | None, haystack_parts: list[str]) -> float:
    if not needle:
        return 0.55
    query = normalize_text(needle)
    haystack = " ".join(normalize_text(part) for part in haystack_parts if part)
    if not haystack:
        return 0.0
    if query in haystack:
        return 1.0
    query_terms = [term for term in query.replace("/", " ").replace(",", " ").split() if term]
    if not query_terms:
        return 0.55
    hits = sum(1 for term in query_terms if term in haystack)
    return clamp(hits / len(query_terms))


def taste_score(taste_tags: list[str] | None, item: FoodCatalogEntry) -> float:
    if not taste_tags:
        return 0.55
    haystack = " ".join(
        normalize_text(part)
        for part in [
            item.name,
            item.description,
            item.category,
            item.cuisine,
            " ".join(item.taste_tags),
            " ".join(item.ingredient_tags),
        ]
        if part
    )
    if not haystack:
        return 0.0
    hits = sum(1 for tag in taste_tags if normalize_text(tag) in haystack)
    return clamp(hits / len(taste_tags))


def budget_score(price: int | None, budget_min: int | None, budget_max: int | None) -> float:
    if price is None:
        return 0.55
    if budget_min is not None and price < budget_min:
        return 0.65
    if budget_max is None:
        return 0.8
    if price <= budget_max:
        return 1.0
    return clamp(1 - ((price - budget_max) / max(budget_max, 1)))


def hard_filter(item: FoodCatalogEntry, request: FoodRecommendationRequest, distance_km: float) -> bool:
    if distance_km > request.max_distance_km:
        return False
    service_radius = item.service_radius_km
    if service_radius is not None and distance_km > service_radius:
        return False
    price = item.final_price or item.price
    if request.budget_max is not None and price is not None and price > request.budget_max * 1.25:
        return False
    return True


def rank_catalog(
    catalog: list[FoodCatalogEntry],
    request: FoodRecommendationRequest,
    recall_scores: dict[str, float] | None = None,
) -> list[FoodRecommendation]:
    recall_scores = recall_scores or {}
    ranked = []
    for item in catalog:
        if item.merchant_lat is None or item.merchant_lng is None:
            continue
        distance = haversine_km(request.lat, request.lng, item.merchant_lat, item.merchant_lng)
        if not hard_filter(item, request, distance):
            continue

        delivery_fee = estimate_delivery_fee(item, distance)
        eta_minutes = estimate_eta(item, distance)
        price = item.final_price or item.price
        breakdown = ScoreBreakdown(
            recall_score=clamp(recall_scores.get(item.item_id, 0.0)),
            nearby_score=clamp(1 - (distance / max(request.max_distance_km, 0.1))),
            delivery_fee_score=clamp(1 - (delivery_fee / 50000)),
            eta_score=clamp(1 - (eta_minutes / 60)),
            budget_score=budget_score(price, request.budget_min, request.budget_max),
            discount_score=clamp((item.discount_percent or 0) / 50),
            category_score=match_score(request.category, [item.name, item.category or "", item.cuisine or ""]),
            taste_score=taste_score(request.taste_tags, item),
            rating_score=normalized_rating(item.merchant_rating),
            popularity_score=clamp(math.log10((item.merchant_review_count or 0) + 1) / 4),
        )
        score = (
            0.16 * breakdown.recall_score
            + 0.20 * breakdown.nearby_score
            + 0.12 * breakdown.delivery_fee_score
            + 0.10 * breakdown.eta_score
            + 0.12 * breakdown.budget_score
            + 0.08 * breakdown.discount_score
            + 0.08 * breakdown.category_score
            + 0.06 * breakdown.taste_score
            + 0.05 * breakdown.rating_score
            + 0.03 * breakdown.popularity_score
        )
        ranked.append(
            FoodRecommendation(
                item_id=item.item_id,
                name=item.name,
                merchant_name=item.merchant_name,
                address=item.merchant_address,
                lat=item.merchant_lat,
                lng=item.merchant_lng,
                distance_km=round(distance, 2),
                price=item.price,
                discount_percent=item.discount_percent,
                final_price=item.final_price,
                rating=item.merchant_rating,
                review_count=item.merchant_review_count,
                delivery_fee=delivery_fee,
                eta_minutes=eta_minutes,
                image_url=item.image_url,
                order_url=item.source_url,
                score=round(score, 4),
                reason=build_reason(item, distance, request, breakdown),
                score_breakdown=breakdown,
            )
        )
    return sorted(ranked, key=lambda item: item.score, reverse=True)[: request.limit]


def build_reason(
    item: FoodCatalogEntry,
    distance_km: float,
    request: FoodRecommendationRequest,
    breakdown: ScoreBreakdown,
) -> str:
    reasons = [f"cách khoảng {distance_km:.1f} km"]
    if request.category and breakdown.category_score > 0:
        reasons.append(f"khớp nhu cầu '{request.category}'")
    if request.budget_max and (item.final_price or item.price):
        reasons.append("hợp ngân sách")
    if item.merchant_rating is not None:
        reasons.append("có tín hiệu đánh giá tốt")
    if item.discount_percent:
        reasons.append(f"đang giảm {item.discount_percent}%")
    return ", ".join(reasons) + "."
