from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Any

from app.db.database import get_db
from app.db.models import FoodRequestLog

router = APIRouter()

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
        data.append({
            "trace_id": t.trace_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "original_query": t.original_query,
            "rewritten_query": t.rewritten_query,
            "intent": t.intent,
            "nlu_json": t.nlu_json,
            "user_context_json": t.user_context_json,
            "location_json": t.location_json,
            "candidate_stats_json": t.candidate_stats_json,
            "ranking_json": t.ranking_json,
            "answer_llm_json": t.answer_llm_json,
            "sse_events_json": t.sse_events_json,
            "latency_json": t.latency_json,
        })
    return {"total": total, "items": data}
