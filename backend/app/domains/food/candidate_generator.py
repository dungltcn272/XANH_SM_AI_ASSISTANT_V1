from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db.models import MerchantMenuItem
from app.domains.food.schemas import FoodCandidate, FoodSearchContext


def _tokenize(text: str) -> list[str]:
    import re

    return re.findall(r"[\wÀ-ỹ]+", (text or "").casefold())


@lru_cache(maxsize=1)
def _jsonl_catalog() -> list[dict]:
    path = Path(settings.DATA_DIR) / "food_catalog" / "shopeefood_catalog.jsonl"
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _candidate_from_mapping(row: dict) -> FoodCandidate:
    tags = []
    for key in ("taste_tags", "diet_tags", "ingredient_tags", "tags"):
        value = row.get(key)
        if isinstance(value, list):
            tags.extend(str(item) for item in value)
    return FoodCandidate(
        item_id=row.get("item_id") or str(row.get("id") or ""),
        name=row.get("name") or row.get("merchant_name") or "Món ăn",
        merchant_name=row.get("merchant_name"),
        category=row.get("category"),
        cuisine=row.get("cuisine"),
        price=row.get("price"),
        final_price=row.get("final_price") or row.get("price"),
        currency=row.get("currency") or "VND",
        image_url=row.get("image_url"),
        source_url=row.get("source_url"),
        merchant_address=row.get("merchant_address"),
        merchant_lat=row.get("merchant_lat"),
        merchant_lng=row.get("merchant_lng"),
        merchant_rating=row.get("merchant_rating"),
        merchant_review_count=row.get("merchant_review_count"),
        tags=list(dict.fromkeys(tags)),
    )


def _db_candidates(db: Session | None, limit: int = 1000) -> list[FoodCandidate]:
    if db is None:
        return []
    rows = db.query(MerchantMenuItem).filter(MerchantMenuItem.status == "active").limit(limit).all()
    return [
        _candidate_from_mapping(
            {
                "item_id": row.item_id or row.id,
                "name": row.name,
                "merchant_name": row.merchant_name,
                "category": row.category,
                "cuisine": row.cuisine,
                "price": row.price,
                "final_price": row.final_price,
                "currency": row.currency,
                "image_url": row.image_url,
                "source_url": row.source_url,
                "merchant_address": row.merchant_address,
                "merchant_lat": row.merchant_lat,
                "merchant_lng": row.merchant_lng,
                "merchant_rating": row.merchant_rating,
                "merchant_review_count": row.merchant_review_count,
                "taste_tags": json.loads(row.taste_tags_json or "[]"),
                "diet_tags": json.loads(row.diet_tags_json or "[]"),
                "ingredient_tags": json.loads(row.ingredient_tags_json or "[]"),
            }
        )
        for row in rows
    ]


def generate_food_candidates(query: str, *, db: Session | None = None, context: FoodSearchContext | None = None, limit: int = 80) -> list[FoodCandidate]:
    candidates = _db_candidates(db)
    if not candidates:
        candidates = [_candidate_from_mapping(row) for row in _jsonl_catalog()]
    if not candidates:
        return []

    corpus = [
        _tokenize(" ".join([item.name, item.merchant_name or "", item.category or "", item.cuisine or "", " ".join(item.tags)]))
        for item in candidates
    ]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
    output = []
    for index, score in ranked[: max(limit * 3, limit)]:
        candidate = candidates[index]
        candidate.score_breakdown["keyword_score"] = float(score)
        output.append(candidate)
    return output[: max(limit * 3, limit)]
