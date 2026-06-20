from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import FoodCatalog
from app.food_recommendation.core.schemas import FoodCatalogEntry


def parse_json_value(value, default):
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def default_catalog_path() -> Path:
    return Path(settings.DATA_DIR or "./data") / "food_catalog" / "shopeefood_catalog.jsonl"


def load_catalog(db: Session | None = None, json_path: str | Path | None = None) -> list[FoodCatalogEntry]:
    if db is not None:
        try:
            rows = db.query(FoodCatalog).all()
            if rows:
                return [entry_from_db(row) for row in rows]
        except Exception:
            # Deploys can still serve food recommendations from the committed JSONL
            # before the admin import has run or when the DB is temporarily unavailable.
            pass
    return load_catalog_from_jsonl(Path(json_path) if json_path else default_catalog_path())


def load_catalog_from_jsonl(path: Path) -> list[FoodCatalogEntry]:
    if not path.exists():
        return []
    entries = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(entry_from_mapping(json.loads(line)))
            except (json.JSONDecodeError, ValueError):
                continue
    return entries


def entry_from_db(row: FoodCatalog) -> FoodCatalogEntry:
    return FoodCatalogEntry(
        item_id=row.item_id,
        name=row.name,
        description=row.description,
        category=row.category,
        cuisine=row.cuisine,
        taste_tags=parse_json_value(row.taste_tags_json, []),
        diet_tags=parse_json_value(row.diet_tags_json, []),
        ingredient_tags=parse_json_value(row.ingredient_tags_json, []),
        price=row.price,
        discount_percent=row.discount_percent,
        final_price=row.final_price,
        currency=row.currency or "VND",
        image_url=row.image_url,
        merchant_id=row.merchant_id,
        merchant_name=row.merchant_name,
        merchant_rating=row.merchant_rating,
        merchant_review_count=row.merchant_review_count,
        merchant_address=row.merchant_address,
        merchant_lat=row.merchant_lat,
        merchant_lng=row.merchant_lng,
        merchant_open_hours=parse_json_value(row.merchant_open_hours_json, None),
        avg_prep_minutes=row.avg_prep_minutes,
        base_delivery_fee=row.base_delivery_fee,
        fee_per_km=row.fee_per_km,
        service_radius_km=row.service_radius_km,
        source=row.source or "shopeefood",
        source_url=row.source_url,
        city=row.city,
        city_slug=row.city_slug,
        last_seen_at=row.last_seen_at.isoformat() if row.last_seen_at else None,
    )


def entry_from_mapping(row: dict) -> FoodCatalogEntry:
    return FoodCatalogEntry(
        item_id=row["item_id"],
        name=row["name"],
        description=row.get("description"),
        category=row.get("category"),
        cuisine=row.get("cuisine"),
        taste_tags=ensure_list(row.get("taste_tags")),
        diet_tags=ensure_list(row.get("diet_tags")),
        ingredient_tags=ensure_list(row.get("ingredient_tags")),
        price=row.get("price"),
        discount_percent=row.get("discount_percent"),
        final_price=row.get("final_price"),
        currency=row.get("currency") or "VND",
        image_url=row.get("image_url"),
        merchant_id=row.get("merchant_id"),
        merchant_name=row.get("merchant_name"),
        merchant_rating=row.get("merchant_rating"),
        merchant_review_count=row.get("merchant_review_count"),
        merchant_address=row.get("merchant_address"),
        merchant_lat=row.get("merchant_lat"),
        merchant_lng=row.get("merchant_lng"),
        merchant_open_hours=row.get("merchant_open_hours"),
        avg_prep_minutes=row.get("avg_prep_minutes"),
        base_delivery_fee=row.get("base_delivery_fee"),
        fee_per_km=row.get("fee_per_km"),
        service_radius_km=row.get("service_radius_km"),
        source=row.get("source") or "shopeefood",
        source_url=row.get("source_url"),
        city=row.get("city"),
        city_slug=row.get("city_slug"),
        last_seen_at=row.get("last_seen_at"),
    )


def ensure_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value if item is not None]
    return []
