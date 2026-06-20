import os
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import String, Text, case, or_, text
from app.db.database import get_db, Base
from app.db.models import RagRequestLog, User, Conversation, DocumentChunk, ErrorLog, CrawlSource, EvaluationRun, BasicRequestLog, FoodInteraction, FoodRequestLog, SemanticCache, SystemLog
from app.core.config import settings
from fastapi.responses import StreamingResponse
import asyncio
from typing import Optional

from app.api.admin.utils import _iso, _json_text_with_defaults
from app.api.admin.serializers import (
    serialize_rag_log,
    serialize_basic_log,
    serialize_food_interaction,
    serialize_food_request_log,
    serialize_system_log
)

router = APIRouter()


def activity_row(raw: dict, intent: str, icon_type: str = "chat") -> dict:
    created_at = raw.get("created_at")
    latency_ms = raw.get("total_latency_ms") or 0
    status = "Blocked" if raw.get("blocked_by_guardrail") else "Success"
    raw_intent = (raw.get("intent") or "").lower()
    fallback_model = settings.RAG_ANSWER_MODEL
    if raw_intent == "food_recommendation":
        fallback_model = settings.FOOD_ANSWER_MODEL
    elif raw_intent in {"small-talk", "missing_info", "sensitive", "blocked_guardrail"}:
        fallback_model = settings.NLU_MODEL
    elif raw_intent == "faq":
        fallback_model = "semantic_cache"
    return {
        **raw,
        "time": created_at[11:19] if isinstance(created_at, str) and len(created_at) >= 19 else "",
        "type": icon_type,
        "query": raw.get("original_query") or raw.get("query") or raw.get("event_type") or "",
        "intent": intent,
        "status": status,
        "latency": f"{latency_ms:.0f}ms" if latency_ms else "-",
        "model": raw.get("model_name") or raw.get("answer_model") or fallback_model,
        "source": raw.get("user_id") or raw.get("guest_id") or raw.get("session_id") or "unknown",
    }


def _hour_bucket(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def build_timeseries(db: Session) -> dict:
    end = datetime.utcnow()
    start = end - timedelta(hours=23)
    buckets = [_hour_bucket(start + timedelta(hours=i)) for i in range(24)]
    data = {
        bucket.strftime("%H:00"): {"time": bucket.strftime("%H:00"), "queries": 0, "latency": 0.0, "cost": 0.0, "cache": 0}
        for bucket in buckets
    }
    rows = (
        db.query(BasicRequestLog)
        .filter(BasicRequestLog.created_at >= start)
        .order_by(BasicRequestLog.created_at.asc())
        .all()
    )
    latency_counts = {key: 0 for key in data}
    for row in rows:
        if not row.created_at:
            continue
        key = _hour_bucket(row.created_at.replace(tzinfo=None)).strftime("%H:00")
        if key not in data:
            continue
        data[key]["queries"] += 1
        data[key]["latency"] += row.total_latency_ms or 0
        data[key]["cost"] += row.cost_usd or 0
        if row.intent == "faq" or row.model_name == "semantic_cache":
            data[key]["cache"] += 1
        latency_counts[key] += 1
    for key, item in data.items():
        if latency_counts[key]:
            item["latency"] = item["latency"] / latency_counts[key]
    points = list(data.values())
    return {
        "queries": [{"time": p["time"], "value": p["queries"]} for p in points],
        "latency": [{"time": p["time"], "value": round(p["latency"], 2)} for p in points],
        "cost": [{"time": p["time"], "value": round(p["cost"], 6)} for p in points],
        "cache": [{"time": p["time"], "value": p["cache"]} for p in points],
    }

@router.get("/stats")
def get_db_stats(db: Session = Depends(get_db)):
    # Lấy tổng số request từ BasicRequestLog
    total_requests = db.query(BasicRequestLog).count()
    avg_latency = db.query(func.avg(BasicRequestLog.total_latency_ms)).scalar() or 0.0
    total_cost = db.query(func.sum(BasicRequestLog.cost_usd)).scalar() or 0.0
    cache_hits = (
        db.query(BasicRequestLog)
        .filter(or_(BasicRequestLog.intent == "faq", BasicRequestLog.model_name == "semantic_cache"))
        .count()
    )
    cache_hit_rate = (cache_hits / total_requests * 100) if total_requests else 0.0
    
    # Gom nhóm theo intent
    intent_counts = db.query(BasicRequestLog.intent, func.count(BasicRequestLog.id)).group_by(BasicRequestLog.intent).all()
    
    # Format intentData cho PieChart
    intentData = []
    # Map màu cho từng loại intent
    color_map = {
        "rag": "#00c897",
        "food_recommendation": "#06b6d4",
        "faq": "#3b82f6",
        "small-talk": "#8b5cf6",
        "missing_info": "#f59e0b",
        "sensitive": "#f97316",
        "blocked_guardrail": "#ef4444",
        "unknown": "#9ca3af"
    }
    
    total_blocked = 0
    for intent, count in intent_counts:
        mapped_intent = intent or "unknown"
        if mapped_intent == "blocked_guardrail" or mapped_intent == "sensitive":
            total_blocked += count
            
        intentData.append({
            "name": mapped_intent.upper() if mapped_intent == "rag" or mapped_intent == "faq" else mapped_intent.replace("_", " ").title(),
            "value": count,
            "color": color_map.get(mapped_intent, "#6b7280"),
            "raw_intent": mapped_intent
        })
        
    total_errors = db.query(ErrorLog).count()
    safetyData = [
        {"name": "Passed", "value": max(0, total_requests - total_blocked - total_errors), "color": "#00c897"},
        {"name": "Blocked", "value": total_blocked, "color": "#f59e0b"},
        {"name": "Error", "value": total_errors, "color": "#ef4444"}
    ]
        
    return {
        "total_requests": total_requests,
        "avg_latency": avg_latency,
        "total_cost": total_cost,
        "cache_hit_rate": cache_hit_rate,
        "total_blocked": total_blocked,
        "total_errors": total_errors,
        "intentData": intentData,
        "safetyData": safetyData,
        "timeseries": build_timeseries(db)
    }


@router.get("/logs")
def get_admin_logs(
    skip: int = 0,
    limit: int = 50,
    intent: Optional[str] = None,
    db: Session = Depends(get_db)
):
    normalized_intent = (intent or "").lower()
    query = db.query(BasicRequestLog)
    if normalized_intent not in ("", "all"):
        query = query.filter(BasicRequestLog.intent == intent)

    logs = (
        query
        .order_by(BasicRequestLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    rows = []
    for row in logs:
        raw_intent = row.intent or "unknown"
        label = raw_intent.upper() if raw_intent in {"rag", "faq"} else raw_intent.replace("_", " ").title()
        rows.append(activity_row(serialize_basic_log(row), label))
    return rows


@router.get("/logs/rag")
def get_rag_logs(skip: int = 0, limit: int = 50, date: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(RagRequestLog)
    if date:
        # Giả định date format 'YYYY-MM-DD'
        query = query.filter(func.date(RagRequestLog.created_at) == date)
    logs = [serialize_rag_log(row) for row in query.order_by(RagRequestLog.created_at.desc()).offset(skip).limit(limit).all()]
    total = query.count()
    return {"logs": logs, "items": logs, "total": total}

@router.get("/logs/basic")
def get_basic_logs(skip: int = 0, limit: int = 50, intent: Optional[str] = None, date: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(BasicRequestLog)
    if intent and intent != "all":
        query = query.filter(BasicRequestLog.intent == intent)
    if date:
        query = query.filter(func.date(BasicRequestLog.created_at) == date)
    logs = [serialize_basic_log(row) for row in query.order_by(BasicRequestLog.created_at.desc()).offset(skip).limit(limit).all()]
    total = query.count()
    return {"logs": logs, "items": logs, "total": total}

@router.get("/logs/food")
def get_food_logs(skip: int = 0, limit: int = 50, date: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(FoodRequestLog)
    if date:
        query = query.filter(func.date(FoodRequestLog.created_at) == date)
    logs = [serialize_food_request_log(row) for row in query.order_by(FoodRequestLog.created_at.desc()).offset(skip).limit(limit).all()]
    total = query.count()
    return {"logs": logs, "items": logs, "total": total}


@router.get("/logs/system")
def get_system_logs(
    skip: int = 0,
    limit: int = 100,
    conversation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    node: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(SystemLog)
    if conversation_id:
        query = query.filter(SystemLog.conversation_id == conversation_id)
    if trace_id:
        query = query.filter(SystemLog.trace_id == trace_id)
    if node:
        query = query.filter(SystemLog.node == node)
    if date:
        query = query.filter(func.date(SystemLog.created_at) == date)
    logs = [serialize_system_log(row) for row in query.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit).all()]
    total = query.count()
    return {"logs": logs, "items": logs, "total": total}


@router.get("/users")
def get_admin_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).limit(500).all()
    return [
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value if user.role else None,
            "created_at": _iso(user.created_at),
        }
        for user in users
    ]


class PipelineTestRequest(BaseModel):
    query: str


@router.post("/pipeline/test")
def test_pipeline(req: PipelineTestRequest):
    from app.nlu.classifier import XanhSMClassifier

    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    classifier = XanhSMClassifier()
    result = classifier.unified_nlu(req.query)
    return {"success": True, "query": req.query, "classification": result}


@router.get("/health")
def get_system_health(db: Session = Depends(get_db)):
    services = []

    def add_service(name: str, ok: bool, detail: str = ""):
        services.append({
            "name": name,
            "status": "healthy" if ok else "down",
            "detail": detail,
        })

    try:
        db.execute(text("SELECT 1"))
        add_service("Database", True)
    except Exception as exc:
        add_service("Database", False, str(exc))

    try:
        from app.vectordb.qdrant_client import COLLECTION_NAME, vectordb

        info = vectordb.qdrant.get_collection(COLLECTION_NAME)
        points_count = getattr(info, "points_count", None)
        add_service("Vector DB", True, f"{points_count or 0} points")
    except Exception as exc:
        add_service("Vector DB", False, str(exc))

    llm_ready = bool(settings.OPENAI_API_KEY or settings.GROQ_API_KEY)
    add_service("LLM API", llm_ready, settings.RAG_ANSWER_MODEL if llm_ready else "No API key configured")

    try:
        cache_count = db.query(SemanticCache).count()
        add_service("Semantic Cache", True, f"{cache_count} entries")
    except Exception as exc:
        add_service("Semantic Cache", False, str(exc))

    try:
        enabled_sources = db.query(CrawlSource).filter(CrawlSource.enabled == True).count()
        add_service("Crawlers", enabled_sources > 0, f"{enabled_sources} enabled sources")
    except Exception as exc:
        add_service("Crawlers", False, str(exc))

    healthy_count = sum(1 for service in services if service["status"] == "healthy")
    score = round((healthy_count / len(services)) * 100, 1) if services else 0.0
    return {
        "score": score,
        "status": "operational" if score >= 80 else "degraded",
        "services": services,
    }


KEYWORD_COLUMN_WEIGHTS = {
    "content": 100,
    "description": 90,
    "message": 80,
    "details": 75,
    "final_answer": 70,
    "original_query": 70,
    "rewritten_query": 65,
    "query": 65,
    "summary": 60,
    "title": 45,
    "section": 40,
    "source": 35,
    "email": 25,
    "name": 25,
}


def _is_searchable_text_column(column) -> bool:
    return isinstance(column.type, (String, Text))


def _parse_search_columns(search_columns: str, table) -> list[str]:
    if search_columns:
        requested = [c.strip() for c in search_columns.split(",") if c.strip()]
        return [
            col_name for col_name in requested
            if col_name in table.columns and _is_searchable_text_column(table.columns[col_name])
        ]

    weighted_cols = [
        col.name for col in table.columns
        if _is_searchable_text_column(col) and col.name in KEYWORD_COLUMN_WEIGHTS
    ]
    other_text_cols = [
        col.name for col in table.columns
        if _is_searchable_text_column(col) and col.name not in KEYWORD_COLUMN_WEIGHTS
    ]
    return sorted(
        weighted_cols,
        key=lambda name: KEYWORD_COLUMN_WEIGHTS.get(name, 1),
        reverse=True
    ) + other_text_cols

# --- DATABASE MANAGER ENDPOINTS ---

@router.get("/db/tables")
def get_db_tables(db: Session = Depends(get_db)):
    metadata = Base.metadata
    return list(metadata.tables.keys())

@router.get("/db/table/{table_name}")
def get_table_data(
    table_name: str, 
    limit: int = 50, 
    offset: int = 0, 
    sort_by: str = None,
    sort_order: str = "desc",
    start_date: str = None,
    end_date: str = None,
    level: str = None,
    error_type: str = None,
    keyword: str = None,
    search_columns: str = None,
    db: Session = Depends(get_db)
):
    metadata = Base.metadata
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail="Table not found")
        
    table = metadata.tables[table_name]
    
    # Build query
    query = db.query(table)
    
    # Apply date filters if date column exists
    date_col = None
    for col_name in ["created_at", "timestamp", "generated_at"]:
        if col_name in table.columns:
            date_col = table.columns[col_name]
            break
            
    if date_col is not None:
        if start_date:
            try:
                from datetime import datetime
                s_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(date_col >= s_dt)
            except Exception:
                pass
        if end_date:
            try:
                from datetime import datetime, time
                e_dt = datetime.strptime(end_date, "%Y-%m-%d")
                e_dt = datetime.combine(e_dt.date(), time(23, 59, 59, 999999))
                query = query.filter(date_col <= e_dt)
            except Exception:
                pass

    # Apply level/error_type exact filters if columns exist
    if level:
        if "level" in table.columns:
            query = query.filter(table.columns["level"] == level)
        elif "error_stage" in table.columns:
            query = query.filter(table.columns["error_stage"] == level)
            
    if error_type:
        if "error_type" in table.columns:
            query = query.filter(table.columns["error_type"] == error_type)
        elif "error_cause" in table.columns:
            query = query.filter(table.columns["error_cause"] == error_type)

    # Apply keyword search across safe text columns. The default set gives
    # higher priority to knowledge text such as document_chunks.content.
    searched_columns = []
    keyword_score_expr = None
    clean_keyword = keyword.strip() if keyword else ""
    if clean_keyword:
        searched_columns = _parse_search_columns(search_columns, table)
        if searched_columns:
            pattern = f"%{clean_keyword}%"
            match_conditions = []
            score_cases = []
            for col_name in searched_columns:
                col = table.columns[col_name]
                condition = col.ilike(pattern)
                match_conditions.append(condition)
                score_cases.append(
                    case(
                        (condition, KEYWORD_COLUMN_WEIGHTS.get(col_name, 10)),
                        else_=0
                    )
                )

            query = query.filter(or_(*match_conditions))
            keyword_score_expr = sum(score_cases)

    # Get total count after filtering
    total = db.query(func.count()).select_from(query.subquery()).scalar()
    
    # Sorting column selection
    sort_col = None
    if sort_by and sort_by in table.columns:
        sort_col = table.columns[sort_by]
    else:
        # Fallback to date column if exists, otherwise first column
        if date_col is not None:
            sort_col = date_col
        elif len(table.columns) > 0:
            sort_col = list(table.columns.values())[0]
            
    if keyword_score_expr is not None:
        query = query.order_by(keyword_score_expr.desc())

    if sort_col is not None:
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())
            
    rows = query.offset(offset).limit(limit).all()
    # Convert Row objects to dicts
    data = [dict(row._mapping) for row in rows]
    
    # Extract dynamic metadata for unique choices (like levels or error types)
    extra_metadata = {}
    if "level" in table.columns:
        distinct_levels = db.query(table.columns["level"]).distinct().all()
        extra_metadata["levels"] = [r[0] for r in distinct_levels if r[0]]
    elif "error_stage" in table.columns:
        distinct_levels = db.query(table.columns["error_stage"]).distinct().all()
        extra_metadata["levels"] = [r[0] for r in distinct_levels if r[0]]
        
    if "error_type" in table.columns:
        distinct_error_types = db.query(table.columns["error_type"]).distinct().all()
        extra_metadata["error_types"] = [r[0] for r in distinct_error_types if r[0]]
    elif "error_cause" in table.columns:
        distinct_error_types = db.query(table.columns["error_cause"]).distinct().all()
        extra_metadata["error_types"] = [r[0] for r in distinct_error_types if r[0]]
    if searched_columns:
        extra_metadata["search_columns"] = searched_columns
        
    return {
        "total": total,
        "data": data,
        "columns": [c.name for c in table.columns],
        "metadata": extra_metadata
    }

class DeleteRecordsRequest(BaseModel):
    ids: list[str]

@router.post("/db/table/{table_name}/delete")
def delete_table_data(table_name: str, req: DeleteRecordsRequest, db: Session = Depends(get_db)):
    metadata = Base.metadata
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail="Table not found")
        
    table = metadata.tables[table_name]
    
    if 'id' not in table.columns:
        raise HTTPException(status_code=400, detail="Table does not have an 'id' column")
        
    stmt = table.delete().where(table.columns.id.in_(req.ids))
    result = db.execute(stmt)
    db.commit()
    
    return {"success": True, "deleted_count": result.rowcount}

@router.post("/db/table/{table_name}/delete_all")
def delete_all_table_data(table_name: str, db: Session = Depends(get_db)):
    metadata = Base.metadata
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail="Table not found")
        
    table = metadata.tables[table_name]
    stmt = table.delete()
    result = db.execute(stmt)
    db.commit()
    
    return {"success": True, "deleted_count": result.rowcount}
