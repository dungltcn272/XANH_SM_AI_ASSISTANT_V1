from __future__ import annotations

from sqlalchemy.orm import Session

from app.food_recommendation.catalog import load_catalog
from app.food_recommendation.ranker import rank_catalog
from app.food_recommendation.retrieval import generate_candidates
from app.food_recommendation.schemas import FoodRecommendation, FoodRecommendationRequest


def recommend_food(
    lat: float,
    lng: float,
    category: str | None = None,
    taste_tags: list[str] | None = None,
    budget_min: int | None = None,
    budget_max: int | None = None,
    meal_time: str | None = None,
    max_distance_km: float = 4,
    user_id: str | None = None,
    limit: int = 5,
    db: Session | None = None,
    query_text: str | None = None,
    metrics: dict | None = None,
) -> list[FoodRecommendation]:
    request = FoodRecommendationRequest(
        lat=lat,
        lng=lng,
        query_text=query_text,
        category=category,
        taste_tags=taste_tags or [],
        budget_min=budget_min,
        budget_max=budget_max,
        meal_time=meal_time,
        max_distance_km=max_distance_km,
        user_id=user_id,
        limit=limit,
    )
    catalog = load_catalog(db=db)
    candidates = generate_candidates(catalog, request, candidate_limit=max(200, limit * 50))
    if metrics is not None:
        metrics["food_retrieval"] = candidates.meta
    return rank_catalog(candidates.items, request, recall_scores=candidates.recall_scores)
