import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import String, Text, case, or_
from app.db.database import get_db, Base
from app.db.models import RagRequestLog, User, Conversation, DocumentChunk, SystemLog, CrawlSource, EvaluationRun
from app.core.config import settings
from fastapi.responses import StreamingResponse
import asyncio
from typing import Optional

router = APIRouter()

class PipelineTestRequest(BaseModel):
    query: str


@router.post("/pipeline/test")
def test_pipeline(req: PipelineTestRequest):
    from app.rag.chain import XanhSMRAGPipeline
    pipeline = XanhSMRAGPipeline()
    try:
        res = pipeline.run_debug(query=req.query)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_requests = db.query(RagRequestLog).count()
    total_conversations = db.query(Conversation).count()
    total_blocked = db.query(RagRequestLog).filter(RagRequestLog.blocked_by_guardrail == True).count()
    
    avg_lat = db.query(func.avg(RagRequestLog.total_latency_ms)).scalar()
    avg_latency = float(avg_lat) if avg_lat else 0.0

    # Calculate total cost of all LLM calls
    total_cost_res = db.query(func.sum(RagRequestLog.cost_usd)).scalar()
    total_cost = float(total_cost_res) if total_cost_res else 0.0

    # Count system errors
    total_errors = db.query(SystemLog).filter(SystemLog.level == "ERROR").count()

    return {
        "total_users": total_users,
        "total_requests": total_requests,
        "total_conversations": total_conversations,
        "total_blocked": total_blocked,
        "avg_latency": avg_latency / 1000.0,  # Convert ms to s for UI
        "total_cost": total_cost,
        "total_errors": total_errors
    }

@router.get("/logs")
def get_rag_logs(intent: str = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(RagRequestLog)
    if intent:
        query = query.filter(RagRequestLog.intent == intent)
    logs = query.order_by(RagRequestLog.created_at.desc()).limit(limit).all()
    return logs

@router.get("/system-logs")
def get_system_logs(limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(SystemLog).order_by(SystemLog.timestamp.desc()).limit(limit).all()
    return logs


@router.get("/users")
def get_users(limit: int = 50, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
    return users

