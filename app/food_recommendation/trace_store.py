from __future__ import annotations

import json
from typing import Any

from app.core.logger import log_warn
from app.db.models import FoodRecommendationTrace


def save_food_recommendation_trace(
    *,
    conversation_id: str | None,
    user_id: str | None,
    guest_id: str | None,
    query: str,
    metrics: dict[str, Any],
    food_context: dict[str, Any] | None,
    slots: Any,
    items: list[Any],
    answer_meta: dict[str, Any] | None,
    sse_steps: list[str],
) -> str | None:
    try:
        from app.db.database import SessionLocal

        db = SessionLocal()
        try:
            trace = FoodRecommendationTrace(
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                original_query=query,
                rewritten_query=metrics.get("rewritten_query") or query,
                intent="food_recommendation",
                nlu_json=json.dumps({
                    "food_slots": metrics.get("food_slots"),
                    "missing_fields": metrics.get("nlu_missing_fields", []),
                }, ensure_ascii=False),
                user_context_json=json.dumps(food_context or {}, ensure_ascii=False),
                location_json=json.dumps({
                    "lat": slots.lat,
                    "lng": slots.lng,
                    "address_text": slots.address_text,
                    "geocoded_address": metrics.get("food_geocoded_address"),
                    "geocode_source": metrics.get("food_geocode_source"),
                }, ensure_ascii=False),
                candidate_stats_json=json.dumps({
                    "result_count": len(items or []),
                    "fallback": metrics.get("food_fallback"),
                    "retrieval": metrics.get("food_retrieval"),
                }, ensure_ascii=False),
                ranking_json=json.dumps({
                    "ranker_version": "food_weighted_ranker_v2_bm25_geo_profile_ready",
                    "ml_ready_notes": [
                        "BM25 geo recall creates the retrieval layer for later embedding/two-tower recall.",
                        "Score breakdown is logged per item for offline learning-to-rank training.",
                        "food_interactions can become labels for cross-encoder or bandit reranking.",
                    ],
                    "top_item_ids": [item.item_id for item in (items or [])[:8]],
                    "top_scores": [round(float(item.score), 4) for item in (items or [])[:8]],
                    "score_breakdown": [
                        {
                            "item_id": item.item_id,
                            "score_breakdown": item.score_breakdown.model_dump(),
                        }
                        for item in (items or [])[:8]
                    ],
                }, ensure_ascii=False),
                answer_llm_json=json.dumps(answer_meta or {}, ensure_ascii=False),
                sse_events_json=json.dumps(sse_steps, ensure_ascii=False),
                latency_json=json.dumps({
                    "search_latency_ms": metrics.get("search_latency_ms", 0),
                    "generation_latency_ms": metrics.get("generation_latency_ms", 0),
                    "total_latency_ms": metrics.get("total_latency_ms", 0),
                }, ensure_ascii=False),
            )
            db.add(trace)
            db.commit()
            db.refresh(trace)
            return trace.trace_id
        finally:
            db.close()
    except Exception as exc:
        log_warn("FOOD", f"Failed to save recommendation trace: {exc}")
        return None
