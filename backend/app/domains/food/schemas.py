from __future__ import annotations

from pydantic import BaseModel, Field


class FoodSearchContext(BaseModel):
    actor_id: str | None = None
    lat: float | None = None
    lng: float | None = None
    address: str | None = None
    query: str | None = None
    budget_vnd: int | None = None
    radius_km: float | None = None


class FoodCandidate(BaseModel):
    item_id: str | None = None
    name: str
    merchant_name: str | None = None
    category: str | None = None
    cuisine: str | None = None
    price: int | None = None
    final_price: int | None = None
    currency: str = "VND"
    image_url: str | None = None
    source_url: str | None = None
    merchant_address: str | None = None
    merchant_lat: float | None = None
    merchant_lng: float | None = None
    merchant_rating: float | None = None
    merchant_review_count: int | None = None
    distance_km: float | None = None
    eta_minutes: float | None = None
    tags: list[str] = Field(default_factory=list)
    score: float = 0.0
    score_breakdown: dict = Field(default_factory=dict)
