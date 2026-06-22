from __future__ import annotations

from pydantic import BaseModel, Field


class FoodRecommendationRequest(BaseModel):
    lat: float
    lng: float
    query_text: str | None = None
    category: str | None = None
    taste_tags: list[str] = Field(default_factory=list)
    negative_taste_tags: list[str] = Field(default_factory=list)
    budget_min: int | None = None
    budget_max: int | None = None
    meal_time: str | None = None
    max_distance_km: float = 4
    user_id: str | None = None
    limit: int = Field(default=5, ge=1, le=20)
    food_context: dict | None = None


class FoodCatalogEntry(BaseModel):
    item_id: str
    name: str
    description: str | None = None
    category: str | None = None
    cuisine: str | None = None
    taste_tags: list[str] = Field(default_factory=list)
    diet_tags: list[str] = Field(default_factory=list)
    ingredient_tags: list[str] = Field(default_factory=list)
    price: int | None = None
    discount_percent: int | None = None
    final_price: int | None = None
    currency: str = "VND"
    image_url: str | None = None
    merchant_id: str | None = None
    merchant_name: str | None = None
    merchant_rating: float | None = None
    merchant_review_count: int | None = None
    merchant_address: str | None = None
    merchant_lat: float | None = None
    merchant_lng: float | None = None
    merchant_open_hours: dict | list | str | None = None
    avg_prep_minutes: int | None = None
    base_delivery_fee: int | None = None
    fee_per_km: int | None = None
    service_radius_km: float | None = None
    source: str = "shopeefood"
    source_url: str | None = None
    city: str | None = None
    city_slug: str | None = None
    last_seen_at: str | None = None


class ScoreBreakdown(BaseModel):
    recall_score: float = 0.0
    nearby_score: float
    delivery_fee_score: float
    eta_score: float
    budget_score: float
    discount_score: float
    category_score: float
    taste_score: float
    rating_score: float
    popularity_score: float
    personalization_score: float = 0.0


class FoodRecommendation(BaseModel):
    item_id: str
    name: str
    merchant_name: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    distance_km: float
    price: int | None = None
    discount_percent: int | None = None
    final_price: int | None = None
    rating: float | None = None
    review_count: int | None = None
    delivery_fee: int | None = None
    eta_minutes: int | None = None
    image_url: str | None = None
    order_url: str | None = None
    score: float
    reason: str
    breakdown: dict | None = None
    score_breakdown: ScoreBreakdown
