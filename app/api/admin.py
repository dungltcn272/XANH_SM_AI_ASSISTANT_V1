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

class PipelineTestRequest(BaseModel):
    query: str


class CrawlSourceRequest(BaseModel):
    url: str
    title: Optional[str] = ""
    source_profile: str = "main_site"
    source_type: str = "web"
    category: str = "user"
    document_type: str = "service"
    output_dir: Optional[str] = None
    crawl_strategy: str = "default"
    enabled: bool = True
    priority: int = 100
    notes: Optional[str] = ""


class EvaluateRequest(BaseModel):
    description: Optional[str] = None


def serialize_crawl_source(row: CrawlSource) -> dict:
    return {
        "id": row.id,
        "url": row.url,
        "title": row.title,
        "source_profile": row.source_profile,
        "source_type": row.source_type,
        "category": row.category,
        "document_type": row.document_type,
        "output_dir": row.output_dir,
        "crawl_strategy": row.crawl_strategy,
        "enabled": row.enabled,
        "priority": row.priority,
        "notes": row.notes,
        "last_crawled_at": row.last_crawled_at.isoformat() if row.last_crawled_at else None,
        "last_status": row.last_status,
        "last_error": row.last_error,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def build_crawl_sources_query(
    db: Session,
    source_profile: str = None,
    category: str = None,
    enabled: Optional[bool] = None,
    keyword: str = None,
):
    query = db.query(CrawlSource)
    if source_profile:
        query = query.filter(CrawlSource.source_profile == source_profile)
    if category:
        query = query.filter(CrawlSource.category == category)
    if enabled is not None:
        query = query.filter(CrawlSource.enabled == enabled)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(or_(
            CrawlSource.url.ilike(pattern),
            CrawlSource.title.ilike(pattern),
            CrawlSource.notes.ilike(pattern),
            CrawlSource.category.ilike(pattern),
            CrawlSource.document_type.ilike(pattern),
        ))
    return query


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
                model_name=settings.LLM_MODEL,
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

@router.get("/data")
def get_data_explorer():
    data_dir = "./data"
    result = []
    if not os.path.exists(data_dir):
        return result
        
    for root, dirs, files in os.walk(data_dir):
        # relative path
        rel_path = os.path.relpath(root, data_dir)
        if rel_path == ".":
            rel_path = "root"
            
        folder_data = {
            "folder": rel_path,
            "files": []
        }
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            folder_data["files"].append({
                "name": file,
                "size": size
            })
        result.append(folder_data)
        
    return result


@router.get("/chunks")
def get_document_chunks(limit: int = 100, db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).order_by(DocumentChunk.created_at.desc()).limit(limit).all()
    return chunks


@router.get("/crawl-sources")
def list_crawl_sources(
    source_profile: str = None,
    category: str = None,
    enabled: Optional[bool] = None,
    keyword: str = None,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    query = build_crawl_sources_query(db, source_profile, category, enabled, keyword)
    rows = query.order_by(CrawlSource.priority.asc(), CrawlSource.created_at.desc()).limit(limit).all()
    return [serialize_crawl_source(row) for row in rows]


@router.get("/crawl-sources/stats")
def get_crawl_sources_stats(
    source_profile: str = None,
    category: str = None,
    enabled: Optional[bool] = None,
    keyword: str = None,
    db: Session = Depends(get_db),
):
    query = build_crawl_sources_query(db, source_profile, category, enabled, keyword)
    total = query.count()
    by_profile = {
        key or "unknown": count
        for key, count in query.with_entities(CrawlSource.source_profile, func.count(CrawlSource.id))
        .group_by(CrawlSource.source_profile)
        .all()
    }
    by_category = {
        key or "unknown": count
        for key, count in query.with_entities(CrawlSource.category, func.count(CrawlSource.id))
        .group_by(CrawlSource.category)
        .all()
    }
    by_type = {
        key or "unknown": count
        for key, count in query.with_entities(CrawlSource.document_type, func.count(CrawlSource.id))
        .group_by(CrawlSource.document_type)
        .all()
    }
    return {
        "total": total,
        "by_profile": by_profile,
        "by_category": by_category,
        "by_type": by_type,
        "is_filtered": any([source_profile, category, enabled is not None, keyword]),
    }


@router.post("/crawl-sources")
def create_crawl_source(req: CrawlSourceRequest, db: Session = Depends(get_db)):
    from crawler.registry import infer_seed

    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    inferred = infer_seed(url, req.category, title=req.title or "", priority=req.priority)
    row = CrawlSource(
        url=inferred.url,
        title=req.title or inferred.title,
        source_profile=req.source_profile or inferred.source_profile,
        source_type=req.source_type or inferred.source_type,
        category=req.category or inferred.category,
        document_type=req.document_type or inferred.document_type,
        output_dir=req.output_dir or f"data/{req.category or inferred.category}",
        crawl_strategy=req.crawl_strategy or inferred.crawl_strategy,
        enabled=req.enabled,
        priority=req.priority,
        notes=req.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_crawl_source(row)


@router.put("/crawl-sources/{source_id}")
def update_crawl_source(source_id: str, req: CrawlSourceRequest, db: Session = Depends(get_db)):
    row = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Crawl source not found")

    for field, value in req.model_dump().items():
        if field == "url" and value:
            value = value.strip()
        if field == "output_dir" and not value:
            value = f"data/{req.category}"
        setattr(row, field, value)

    db.commit()
    db.refresh(row)
    return serialize_crawl_source(row)


@router.delete("/crawl-sources/{source_id}")
def delete_crawl_source(source_id: str, db: Session = Depends(get_db)):
    row = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Crawl source not found")
    db.delete(row)
    db.commit()
    return {"success": True, "deleted_id": source_id}


@router.post("/crawl-sources/bootstrap")
def bootstrap_crawl_sources(db: Session = Depends(get_db)):
    from crawler.registry import bootstrap_from_urls_json

    return bootstrap_from_urls_json(db, only_if_empty=True)


@router.post("/crawl-sources/sync")
def sync_crawl_sources(db: Session = Depends(get_db)):
    from crawler.registry import sync_from_urls_json

    return sync_from_urls_json(db)


@router.post("/knowledge/clear")
def clear_all_knowledge(db: Session = Depends(get_db)):
    from app.ingestion.ingest import setup_qdrant
    from app.vectordb.qdrant_client import vectordb

    chunks_deleted = db.query(DocumentChunk).delete()
    db.commit()
    setup_qdrant(vectordb.qdrant, recreate=True)
    return {
        "success": True,
        "chunks_deleted": chunks_deleted,
        "qdrant_collection_reset": True,
    }


@router.post("/knowledge/ingest-all")
def ingest_all_knowledge():
    from app.core.config import settings
    from app.ingestion.ingest import ingest_data

    data_dir = settings.DATA_DIR or "./data"
    if not os.path.exists(data_dir):
        raise HTTPException(status_code=404, detail=f"Data directory not found: {data_dir}")
    summary = ingest_data(data_dir, reset_collection=False)
    return {"success": True, **summary}

@router.post("/evaluate")
async def evaluate_rag(req: Optional[EvaluateRequest] = None):
    """
    Chạy đánh giá bằng RAGAS. Trả về stream SSE báo cáo tiến độ.
    """
    async def event_generator():
        yield 'data: {"step": "Bắt đầu đánh giá RAGAS..."}\n\n'
        await asyncio.sleep(1)
        yield 'data: {"step": "Đang lấy tập dữ liệu Golden Dataset..."}\n\n'
        
        try:
            import subprocess
            import sys
            import os
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
            env["TQDM_DISABLE"] = "1"
            if req and req.description:
                env["EVAL_DESCRIPTION"] = req.description
            
            process = subprocess.Popen(
                [sys.executable, "-W", "ignore", "-u", "evaluation/ragas_eval.py"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=env
            )
            
            loop = asyncio.get_event_loop()
            
            def read_line():
                return process.stdout.readline()
            
            while True:
                line = await loop.run_in_executor(None, read_line)
                if not line:
                    break
                line_str = line.decode('utf-8', errors='replace').strip()
                if line_str:
                    data_json = json.dumps({"step": line_str}, ensure_ascii=False)
                    yield f"data: {data_json}\n\n"
                    await asyncio.sleep(0.1)
                    
            process.wait()
            if process.returncode == 0:
                yield 'data: {"step": "Đánh giá hoàn tất!"}\n\n'
            else:
                yield 'data: {"error": "Lỗi trong quá trình đánh giá."}\n\n'
        except Exception as e:
            import traceback
            traceback.print_exc()
            err_msg = json.dumps({"error": f"{type(e).__name__}: {str(e)}"}, ensure_ascii=False)
            yield f"data: {err_msg}\n\n"
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/ingest/crawl")
async def run_crawler(max_urls: int = 0):
    """
    Chạy Script Cào Dữ Liệu. Trả về stream SSE báo cáo tiến độ.
    """
    async def event_generator():
        yield 'data: {"step": "Bắt đầu khởi động Web Crawler..."}\n\n'
        
        try:
            import subprocess
            import sys
            import os
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
            env["TQDM_DISABLE"] = "1"
            
            cmd = [sys.executable, "-W", "ignore", "-u", "crawler/run_crawler.py", "--max-urls", str(max(0, max_urls))]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=env
            )
            
            loop = asyncio.get_event_loop()
            
            def read_line():
                return process.stdout.readline()
            
            while True:
                line = await loop.run_in_executor(None, read_line)
                if not line:
                    break
                line_str = line.decode('utf-8', errors='replace').strip()
                if line_str:
                    data_json = json.dumps({"step": line_str}, ensure_ascii=False)
                    yield f"data: {data_json}\n\n"
                    await asyncio.sleep(0.05)
                    
            process.wait()
            if process.returncode == 0:
                yield 'data: {"step": "Cào dữ liệu hoàn tất!"}\n\n'
            else:
                yield 'data: {"error": "Lỗi trong quá trình cào dữ liệu."}\n\n'
        except Exception as e:
            import traceback
            traceback.print_exc()
            err_msg = json.dumps({"error": f"{type(e).__name__}: {str(e)}"}, ensure_ascii=False)
            yield f"data: {err_msg}\n\n"
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/ingest/crawl/agent")
async def run_agent_crawler(max_urls: int = 0):
    """
    Chạy deterministic crawler cho Green SM Platform/PDF. Trả về stream SSE báo cáo tiến độ.
    """
    async def event_generator():
        yield 'data: {"step": "Bắt đầu khởi động Platform/PDF Crawler thuần code..."}\n\n'
        try:
            import subprocess
            import sys
            import os
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            cmd = [
                sys.executable, "-W", "ignore", "-u",
                "crawler/agent_crawler.py",
                "--sources", "platform,platform_pdf",
                "--max-urls", str(max(0, max_urls)),
            ]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=env
            )
            
            loop = asyncio.get_event_loop()
            def read_line():
                return process.stdout.readline()
            
            while True:
                line = await loop.run_in_executor(None, read_line)
                if not line:
                    break
                line_str = line.decode('utf-8', errors='replace').strip()
                if line_str:
                    if "[AGENT_STEP]" in line_str:
                        step_part = line_str.split("[AGENT_STEP]")[-1].strip()
                        yield f'data: {{"step": "[AGENT_STEP] {step_part}"}}\n\n'
                    else:
                        data_json = json.dumps({"step": line_str}, ensure_ascii=False)
                        yield f"data: {data_json}\n\n"
                    await asyncio.sleep(0.01)
                    
            process.wait()
            if process.returncode == 0:
                yield 'data: {"step": "[AGENT_STEP] Complete"}\n\n'
                yield 'data: {"step": "Platform/PDF Crawler hoàn tất!"}\n\n'
            else:
                yield 'data: {"error": "Lỗi trong quá trình chạy Platform/PDF Crawler."}\n\n'
        except Exception as e:
            import traceback
            traceback.print_exc()
            err_msg = json.dumps({"error": f"{type(e).__name__}: {str(e)}"}, ensure_ascii=False)
            yield f"data: {err_msg}\n\n"
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/ingest/process/platform")
async def run_platform_ingestion():
    """
    Chạy nạp dữ liệu (Chunking & Embedding) chỉ cho thư mục data/platform/. Trả về stream SSE báo cáo tiến độ.
    """
    async def event_generator():
        yield 'data: {"step": "Bắt đầu nạp dữ liệu Platform..."}\n\n'
        try:
            import subprocess
            import sys
            import os
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            process = subprocess.Popen(
                [sys.executable, "-W", "ignore", "-u", "app/ingestion/ingest.py", "--category", "platform"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=env
            )
            
            loop = asyncio.get_event_loop()
            def read_line():
                return process.stdout.readline()
            
            while True:
                line = await loop.run_in_executor(None, read_line)
                if not line:
                    break
                line_str = line.decode('utf-8', errors='replace').strip()
                if line_str:
                    data_json = json.dumps({"step": line_str}, ensure_ascii=False)
                    yield f"data: {data_json}\n\n"
                    await asyncio.sleep(0.01)
                    
            process.wait()
            if process.returncode == 0:
                yield 'data: {"step": "Nạp dữ liệu Platform hoàn tất!"}\n\n'
            else:
                yield 'data: {"error": "Lỗi trong quá trình nạp dữ liệu Platform."}\n\n'
        except Exception as e:
            import traceback
            traceback.print_exc()
            err_msg = json.dumps({"error": f"{type(e).__name__}: {str(e)}"}, ensure_ascii=False)
            yield f"data: {err_msg}\n\n"
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/ingest/process")
async def run_ingestion():
    """
    Chạy Script Ingestion (Chunking & Embedding). Trả về stream SSE báo cáo tiến độ.
    """
    async def event_generator():
        yield 'data: {"step": "Bắt đầu Ingestion pipeline..."}\n\n'
        
        try:
            import subprocess
            import sys
            import os
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
            env["TQDM_DISABLE"] = "1"
            
            process = subprocess.Popen(
                [sys.executable, "-W", "ignore", "-u", "app/ingestion/ingest.py"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=env
            )
            
            loop = asyncio.get_event_loop()
            
            def read_line():
                return process.stdout.readline()
            
            while True:
                line = await loop.run_in_executor(None, read_line)
                if not line:
                    break
                line_str = line.decode('utf-8', errors='replace').strip()
                if line_str:
                    data_json = json.dumps({"step": line_str}, ensure_ascii=False)
                    yield f"data: {data_json}\n\n"
                    await asyncio.sleep(0.05)
                    
            process.wait()
            if process.returncode == 0:
                yield 'data: {"step": "Nạp dữ liệu hoàn tất!"}\n\n'
            else:
                yield 'data: {"error": "Lỗi trong quá trình nạp dữ liệu."}\n\n'
        except Exception as e:
            import traceback
            traceback.print_exc()
            err_msg = json.dumps({"error": f"{type(e).__name__}: {str(e)}"}, ensure_ascii=False)
            yield f"data: {err_msg}\n\n"
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
    if level and "level" in table.columns:
        query = query.filter(table.columns["level"] == level)
    if error_type and "error_type" in table.columns:
        query = query.filter(table.columns["error_type"] == error_type)

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
    if "error_type" in table.columns:
        distinct_error_types = db.query(table.columns["error_type"]).distinct().all()
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
