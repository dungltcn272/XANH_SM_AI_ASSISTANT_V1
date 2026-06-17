from __future__ import annotations

from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from app.food_recommendation.profile import normalize_text
from app.food_recommendation.ranker import haversine_km
from app.food_recommendation.schemas import FoodCatalogEntry, FoodRecommendationRequest


@dataclass
class CandidateGenerationResult:
    items: list[FoodCatalogEntry]
    recall_scores: dict[str, float]
    meta: dict


def tokenize(text: str | None) -> list[str]:
    normalized = normalize_text(text or "")
    return [term for term in normalized.replace("/", " ").replace(",", " ").split() if term]


def catalog_document(item: FoodCatalogEntry) -> str:
    return " ".join(
        str(part)
        for part in [
            item.name,
            item.description,
            item.category,
            item.cuisine,
            " ".join(item.taste_tags),
            " ".join(item.diet_tags),
            " ".join(item.ingredient_tags),
            item.merchant_name,
            item.merchant_address,
            item.city,
        ]
        if part
    )


def request_document(request: FoodRecommendationRequest) -> str:
    return " ".join(
        str(part)
        for part in [
            request.query_text,
            request.category,
            " ".join(request.taste_tags or []),
            request.meal_time,
        ]
        if part
    )


def generate_candidates(
    catalog: list[FoodCatalogEntry],
    request: FoodRecommendationRequest,
    *,
    candidate_limit: int = 400,
) -> CandidateGenerationResult:
    geo_candidates: list[FoodCatalogEntry] = []
    geo_radius = max(request.max_distance_km * 3, request.max_distance_km, 12)

    for item in catalog:
        if item.merchant_lat is None or item.merchant_lng is None:
            continue
        distance = haversine_km(request.lat, request.lng, item.merchant_lat, item.merchant_lng)
        if distance <= geo_radius:
            geo_candidates.append(item)

    if not geo_candidates:
        return CandidateGenerationResult(
            items=[],
            recall_scores={},
            meta={
                "retrieval_version": "food_bm25_geo_recall_v1",
                "catalog_size": len(catalog),
                "geo_radius_km": geo_radius,
                "geo_candidate_count": 0,
                "candidate_count": 0,
            },
        )

    query_tokens = tokenize(request_document(request))
    if not query_tokens:
        selected = geo_candidates[:candidate_limit]
        return CandidateGenerationResult(
            items=selected,
            recall_scores={item.item_id: 0.55 for item in selected},
            meta={
                "retrieval_version": "food_bm25_geo_recall_v1",
                "catalog_size": len(catalog),
                "geo_radius_km": geo_radius,
                "geo_candidate_count": len(geo_candidates),
                "candidate_count": len(selected),
                "query_terms": [],
                "recall_mode": "geo_only",
            },
        )

    tokenized_docs = [tokenize(catalog_document(item)) for item in geo_candidates]
    bm25 = BM25Okapi(tokenized_docs)
    raw_scores = bm25.get_scores(query_tokens)
    max_score = max(raw_scores) if len(raw_scores) else 0

    scored = []
    recall_scores: dict[str, float] = {}
    for item, raw_score in zip(geo_candidates, raw_scores):
        normalized_score = float(raw_score / max_score) if max_score > 0 else 0.0
        recall_scores[item.item_id] = normalized_score
        scored.append((normalized_score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    selected = [item for _, item in scored[:candidate_limit]]
    return CandidateGenerationResult(
        items=selected,
        recall_scores={item.item_id: recall_scores.get(item.item_id, 0.0) for item in selected},
        meta={
            "retrieval_version": "food_bm25_geo_recall_v1",
            "catalog_size": len(catalog),
            "geo_radius_km": geo_radius,
            "geo_candidate_count": len(geo_candidates),
            "candidate_count": len(selected),
            "query_terms": query_tokens[:24],
            "recall_mode": "bm25_geo",
        },
    )
