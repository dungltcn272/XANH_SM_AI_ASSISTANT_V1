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

class EvaluateRequest(BaseModel):
    description: Optional[str] = None


@router.get("/eval")
def get_eval_results(db: Session = Depends(get_db)):
    # Try to load the latest evaluation run from the database first
    latest_run = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).first()
    report = None
    if latest_run:
        try:
            report = {
                "metrics": json.loads(latest_run.metrics_json) if latest_run.metrics_json else {},
                "details": json.loads(latest_run.details_json) if latest_run.details_json else []
            }
        except Exception as e:
            pass

    if not report:
        try:
            with open("evaluation_report.json", "r", encoding="utf-8") as f:
                report = json.load(f)
        except FileNotFoundError:
            report = {"error": "Evaluation report not found in DB or file. Please run the benchmark first."}

    try:
        with open("evaluation/golden_dataset.json", "r", encoding="utf-8") as f:
            golden_cases = json.load(f)
            golden_total_cases = len(golden_cases)
    except Exception:
        golden_cases = []
        golden_total_cases = report.get("metrics", {}).get("total_cases", 0)

    report.setdefault("metrics", {})
    report["metrics"]["golden_total_cases"] = golden_total_cases
    report["metrics"]["pending_cases"] = max(0, golden_total_cases - report["metrics"].get("total_cases", 0))

    if golden_cases:
        result_by_id = {
            item.get("id"): item
            for item in report.get("details", [])
            if item.get("id")
        }
        merged_details = []
        for case in golden_cases:
            result = result_by_id.get(case.get("id"))
            if result:
                merged_details.append({**case, **result, "status": "completed"})
            else:
                merged_details.append({
                    **case,
                    "status": "pending",
                    "answer": "",
                    "latency_seconds": None,
                    "retrieval": {},
                    "generation": {},
                    "matched_keywords": [],
                    "num_chunks_before_expansion": 0,
                    "compressed_context_len": 0,
                })
        report["details"] = merged_details
    return report

def serialize_eval_run(row: EvaluationRun) -> dict:
    return {
        "id": row.id,
        "run_name": row.run_name,
        "description": row.description,
        "dataset_name": row.dataset_name,
        "model_name": row.model_name,
        "total_cases": row.total_cases,
        "status": row.status,
        "average_latency_sec": row.average_latency_sec,
        "retrieval": {
            "recall_5": row.recall_5,
            "recall_10": row.recall_10,
            "mrr": row.mrr,
            "ndcg_5": row.ndcg_5,
        },
        "generation": {
            "faithfulness": row.faithfulness,
            "correctness": row.correctness,
            "relevancy": row.relevancy,
        },
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/eval/runs")
def get_eval_runs(limit: int = 20, db: Session = Depends(get_db)):
    from app.db.database import engine
    Base.metadata.create_all(bind=engine)
    if db.query(EvaluationRun).count() == 0 and os.path.exists("evaluation_report.json"):
        try:
            with open("evaluation_report.json", "r", encoding="utf-8") as f:
                report = json.load(f)
            metrics = report.get("metrics", {})
            retrieval = metrics.get("retrieval", {})
            generation = metrics.get("generation", {})
            seed = EvaluationRun(
                run_name=f"legacy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description="Legacy evaluation run snapshot.",
                dataset_name=f"golden_{metrics.get('total_cases', len(report.get('details', [])))}",
                model_name=settings.RAG_ANSWER_MODEL,
                total_cases=metrics.get("total_cases", 0),
                status="completed",
                average_latency_sec=metrics.get("average_latency_sec", 0),
                recall_5=retrieval.get("recall_5", 0),
                recall_10=retrieval.get("recall_10", 0),
                mrr=retrieval.get("mrr", 0),
                ndcg_5=retrieval.get("ndcg_5", 0),
                faithfulness=generation.get("faithfulness", 0),
                correctness=generation.get("correctness", 0),
                relevancy=generation.get("relevancy", 0),
                metrics_json=json.dumps(metrics, ensure_ascii=False),
                details_json=json.dumps(report.get("details", []), ensure_ascii=False),
            )
            db.add(seed)
            db.commit()
        except Exception:
            db.rollback()
    rows = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(limit).all()
    runs = [serialize_eval_run(row) for row in rows]
    chronological = list(reversed(runs))
    latest = runs[0] if runs else None
    previous = runs[1] if len(runs) > 1 else None

    def delta(path: tuple[str, ...]):
        if not latest or not previous:
            return None
        cur = latest
        prev = previous
        for key in path:
            cur = cur.get(key, {}) if isinstance(cur, dict) else {}
            prev = prev.get(key, {}) if isinstance(prev, dict) else {}
        if not isinstance(cur, (int, float)) or not isinstance(prev, (int, float)):
            return None
        return round(cur - prev, 4)

    return {
        "runs": runs,
        "trend": [
            {
                "run_name": item["run_name"],
                "created_at": item["created_at"],
                "recall_5": item["retrieval"]["recall_5"],
                "recall_10": item["retrieval"]["recall_10"],
                "mrr": item["retrieval"]["mrr"],
                "ndcg_5": item["retrieval"]["ndcg_5"],
                "faithfulness": item["generation"]["faithfulness"],
                "correctness": item["generation"]["correctness"],
                "relevancy": item["generation"]["relevancy"],
                "latency": item["average_latency_sec"],
            }
            for item in chronological
        ],
        "delta": {
            "recall_5": delta(("retrieval", "recall_5")),
            "recall_10": delta(("retrieval", "recall_10")),
            "mrr": delta(("retrieval", "mrr")),
            "ndcg_5": delta(("retrieval", "ndcg_5")),
            "faithfulness": delta(("generation", "faithfulness")),
            "correctness": delta(("generation", "correctness")),
            "relevancy": delta(("generation", "relevancy")),
            "average_latency_sec": delta(("average_latency_sec",)),
        },
    }

# Global state to track evaluation job
eval_job = {
    "running": False,
    "logs": [],
    "done": False,
    "error": None
}

import threading

def run_eval_thread(description: str):
    global eval_job
    try:
        from evaluation.ragas_eval import XanhSMEvaluation
        if description:
            os.environ["EVAL_DESCRIPTION"] = description
            
        def queue_print(msg: str):
            eval_job["logs"].append({"step": msg.strip()})
            
        evaluator = XanhSMEvaluation(print_func=queue_print)
        evaluator.run_suite()
        eval_job["done"] = True
    except Exception as e:
        import traceback
        traceback.print_exc()
        eval_job["error"] = f"{type(e).__name__}: {str(e)}"
        eval_job["done"] = True
    finally:
        eval_job["running"] = False

@router.post("/evaluate")
def evaluate_rag_start(req: Optional[EvaluateRequest] = None):
    """
    Starts the evaluation in a background thread to prevent Railway proxy timeouts (100s).
    """
    global eval_job
    if eval_job["running"]:
        return {"status": "already_running"}
        
    eval_job["running"] = True
    eval_job["logs"] = [{"step": "Bắt đầu đánh giá RAGAS..."}]
    eval_job["done"] = False
    eval_job["error"] = None
    
    desc = req.description if req else ""
    thread = threading.Thread(target=run_eval_thread, args=(desc,))
    thread.start()
    
    return {"status": "started"}

@router.get("/evaluate/status")
def evaluate_rag_status(offset: int = 0):
    """
    Returns the evaluation status and logs from the given offset.
    """
    global eval_job
    new_logs = eval_job["logs"][offset:]
    return {
        "running": eval_job["running"],
        "done": eval_job["done"],
        "error": eval_job["error"],
        "logs": new_logs,
        "next_offset": offset + len(new_logs)
    }


