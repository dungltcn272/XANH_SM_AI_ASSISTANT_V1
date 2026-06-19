from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Any
import json

from app.db.database import get_db
from app.db.models import FoodRequestLog

router = APIRouter()


def normalize_candidate_stats(value: str | None) -> str:
    try:
        data = json.loads(value or "{}")
        if not isinstance(data, dict):
            data = {}
    except json.JSONDecodeError:
        data = {}
    result_count = data.get("result_count", 0)
    data.setdefault("returned_count", result_count)
    data.setdefault("total_candidates", result_count)
    return json.dumps(data, ensure_ascii=False)

@router.get("/food-traces")
def get_food_traces(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    total = db.query(FoodRequestLog).count()
    traces = (
        db.query(FoodRequestLog)
        .order_by(desc(FoodRequestLog.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    data = []
    for t in traces:
        latency_json = json.dumps({
            "search_latency_ms": t.search_latency_ms or 0,
            "generation_latency_ms": t.generation_latency_ms or 0,
            "total_latency_ms": t.total_latency_ms or 0,
            "rewrite_latency_ms": t.rewrite_latency_ms or 0,
            "classification_latency_ms": t.classification_latency_ms or 0,
        })
        data.append({
            "trace_id": t.trace_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "conversation_id": t.conversation_id,
            "user_id": t.user_id,
            "guest_id": t.guest_id,
            "original_query": t.original_query,
            "rewritten_query": t.rewritten_query,
            "final_answer": t.final_answer,
            "intent": t.intent,
            "search_latency_ms": t.search_latency_ms or 0,
            "generation_latency_ms": t.generation_latency_ms or 0,
            "total_latency_ms": t.total_latency_ms or 0,
            "rewrite_latency_ms": t.rewrite_latency_ms or 0,
            "classification_latency_ms": t.classification_latency_ms or 0,
            "total_tokens": t.total_tokens or 0,
            "cost_usd": t.cost_usd or 0,
            "nlu_json": t.nlu_json,
            "user_context_json": t.user_context_json,
            "location_json": t.location_json,
            "candidate_stats_json": normalize_candidate_stats(t.candidate_stats_json),
            "ranking_json": t.ranking_json,
            "answer_llm_json": t.answer_llm_json,
            "sse_events_json": t.sse_events_json,
            "latency_json": latency_json,
        })
    return {"total": total, "items": data}
