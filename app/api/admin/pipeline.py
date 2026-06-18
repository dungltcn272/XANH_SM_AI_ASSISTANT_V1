import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import String, Text, case, or_
from app.db.database import get_db, Base
from app.db.models import RagRequestLog, User, Conversation, DocumentChunk, ErrorLog, CrawlSource, EvaluationRun, FoodRequestLog, BasicRequestLog, SemanticCache
from app.core.config import settings
from fastapi.responses import StreamingResponse
import asyncio
from typing import Optional

router = APIRouter()

class PipelineTestRequest(BaseModel):
    query: str


@router.post("/pipeline/test")
def test_pipeline(req: PipelineTestRequest):
    from app.assistant.orchestrator import XanhSMAssistantOrchestrator
    pipeline = XanhSMAssistantOrchestrator()
    try:
        res = pipeline.run_debug(query=req.query)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_conversations = db.query(Conversation).count()
    
    # 1. Intent Data
    rag_count = db.query(RagRequestLog).count()
    food_count = db.query(FoodRequestLog).count()
    
    intent_data_map = {
        "RAG": {"value": rag_count, "color": "#00c897"},
        "Food Recommendation": {"value": food_count, "color": "#06b6d4"},
        "FAQ": {"value": 0, "color": "#3b82f6"},
        "Small Talk": {"value": 0, "color": "#8b5cf6"},
        "Sensitive / Other": {"value": 0, "color": "#f97316"}
    }
    
    basic_logs = db.query(BasicRequestLog.intent, func.count(BasicRequestLog.id)).group_by(BasicRequestLog.intent).all()
    basic_count = 0
    for intent, count in basic_logs:
        basic_count += count
        if intent == "faq": intent_data_map["FAQ"]["value"] += count
        elif intent == "small-talk": intent_data_map["Small Talk"]["value"] += count
        elif intent == "sensitive": intent_data_map["Sensitive / Other"]["value"] += count
        else: intent_data_map["Sensitive / Other"]["value"] += count
        
    intentData = [{"name": k, "value": v["value"], "color": v["color"]} for k, v in intent_data_map.items()]
    total_requests = rag_count + food_count + basic_count
    
    # 2. Safety Data
    total_blocked = db.query(RagRequestLog).filter(RagRequestLog.blocked_by_guardrail == True).count()
    total_errors = db.query(ErrorLog).count()
    total_passed = max(0, total_requests - total_blocked - total_errors)
    safetyData = [
        {"name": "Passed", "value": total_passed, "color": "#00c897"},
        {"name": "Blocked", "value": total_blocked, "color": "#f59e0b"},
        {"name": "Error", "value": total_errors, "color": "#ef4444"}
    ]
    
    # Latency
    rag_lat = db.query(func.avg(RagRequestLog.total_latency_ms)).scalar() or 0.0
    food_lat = db.query(func.avg(FoodRequestLog.total_latency_ms)).scalar() or 0.0
    basic_lat = db.query(func.avg(BasicRequestLog.total_latency_ms)).scalar() or 0.0
    
    avg_latency = 0.0
    if total_requests > 0:
        avg_latency = (rag_lat * rag_count + food_lat * food_count + basic_lat * basic_count) / total_requests

    # Cost
    rag_cost = db.query(func.sum(RagRequestLog.cost_usd)).scalar() or 0.0
    food_cost = db.query(func.sum(FoodRequestLog.cost_usd)).scalar() or 0.0
    total_cost = float(rag_cost) + float(food_cost)

    # Cache hits
    total_cache_entries = db.query(SemanticCache).count()
    cache_hit_rate = (total_cache_entries / total_requests * 100) if total_requests > 0 else 0.0

    return {
        "total_users": total_users,
        "total_requests": total_requests,
        "total_conversations": total_conversations,
        "total_blocked": total_blocked,
        "avg_latency": avg_latency,
        "total_cost": total_cost,
        "total_errors": total_errors,
        "cache_hit_rate": cache_hit_rate,
        "intentData": intentData,
        "safetyData": safetyData
    }

@router.get("/logs")
def get_unified_logs(intent: str = None, limit: int = 50, db: Session = Depends(get_db)):
    # Fetch from all 3 tables and ErrorLog to build activity feed
    rag_logs = db.query(RagRequestLog).order_by(RagRequestLog.created_at.desc()).limit(limit).all()
    food_logs = db.query(FoodRequestLog).order_by(FoodRequestLog.created_at.desc()).limit(limit).all()
    basic_logs = db.query(BasicRequestLog).order_by(BasicRequestLog.created_at.desc()).limit(limit).all()
    
    combined = []
    
    for r in rag_logs:
        if intent and intent.lower() != "rag": continue
        combined.append({
            "id": r.id,
            "created_at": r.created_at,
            "time": r.created_at.strftime("%H:%M:%S") if r.created_at else "-",
            "type": "shield" if r.blocked_by_guardrail else "database",
            "query": r.original_query or "Empty query",
            "intent": "RAG",
            "status": "Blocked" if r.blocked_by_guardrail else "Success",
            "latency": f"{r.total_latency_ms:.0f}ms",
            "model": "GPT-4o-mini",
            "source": "Web Chat"
        })
        
    for f in food_logs:
        if intent and intent.lower() != "food": continue
        combined.append({
            "id": f.trace_id,
            "created_at": f.created_at,
            "time": f.created_at.strftime("%H:%M:%S") if f.created_at else "-",
            "type": "zap",
            "query": f.original_query or "Empty query",
            "intent": "Food",
            "status": "Success",
            "latency": f"{f.total_latency_ms:.0f}ms",
            "model": "GPT-4o-mini",
            "source": "Web Chat"
        })
        
    for b in basic_logs:
        if intent and b.intent != intent: continue
        i_name = "FAQ" if b.intent == "faq" else ("Small Talk" if b.intent == "small-talk" else "Sensitive")
        combined.append({
            "id": b.id,
            "created_at": b.created_at,
            "time": b.created_at.strftime("%H:%M:%S") if b.created_at else "-",
            "type": "chat",
            "query": b.original_query or "Empty query",
            "intent": i_name,
            "status": "Success",
            "latency": f"{b.total_latency_ms:.0f}ms",
            "model": "GPT-4o-mini",
            "source": "Web Chat"
        })
        
    combined.sort(key=lambda x: x["created_at"] if x["created_at"] else datetime.min, reverse=True)
    return combined[:limit]

@router.get("/system-logs")
def get_system_logs(limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(ErrorLog).order_by(ErrorLog.created_at.desc()).limit(limit).all()
    return logs

@router.get("/logs/rag")
def get_rag_logs(skip: int = 0, limit: int = 50, date: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(RagRequestLog)
    if date:
        query = query.filter(RagRequestLog.created_at >= f"{date} 00:00:00")
        query = query.filter(RagRequestLog.created_at <= f"{date} 23:59:59")
    total = query.count()
    logs = query.order_by(RagRequestLog.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": logs}

@router.get("/logs/food")
def get_food_logs(skip: int = 0, limit: int = 50, date: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(FoodRequestLog)
    if date:
        query = query.filter(FoodRequestLog.created_at >= f"{date} 00:00:00")
        query = query.filter(FoodRequestLog.created_at <= f"{date} 23:59:59")
    total = query.count()
    logs = query.order_by(FoodRequestLog.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": logs}

@router.get("/logs/basic")
def get_basic_logs(
    skip: int = 0,
    limit: int = 50,
    intent: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(BasicRequestLog)
    if intent and intent.lower() != "all":
        query = query.filter(BasicRequestLog.intent == intent)
    if date:
        query = query.filter(BasicRequestLog.created_at >= f"{date} 00:00:00")
        query = query.filter(BasicRequestLog.created_at <= f"{date} 23:59:59")
    total = query.count()
    logs = query.order_by(BasicRequestLog.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": logs}


@router.get("/users")
def get_users(limit: int = 50, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
    return users
