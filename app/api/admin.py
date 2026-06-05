import os
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import Table
from app.db.database import get_db, Base
from app.db.models import RagRequestLog, User, Conversation, DocumentChunk, SystemLog
from fastapi.responses import StreamingResponse
import asyncio

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

@router.get("/eval")
def get_eval_results():
    try:
        with open("evaluation_report.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Evaluation report not found. Please run the benchmark first."}

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

@router.post("/evaluate")
async def evaluate_rag():
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
async def run_crawler():
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
            
            process = subprocess.Popen(
                [sys.executable, "-W", "ignore", "-u", "crawler/run_crawler.py"], 
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
async def run_agent_crawler():
    """
    Chạy AI Agentic Crawler cho Green SM Platform. Trả về stream SSE báo cáo tiến độ.
    """
    async def event_generator():
        yield 'data: {"step": "Bắt đầu khởi động AI Agentic Crawler..."}\n\n'
        try:
            import subprocess
            import sys
            import os
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            process = subprocess.Popen(
                [sys.executable, "-W", "ignore", "-u", "crawler/agent_crawler.py", "--max-urls", "45"], 
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
                yield 'data: {"step": "AI Agentic Crawler hoàn tất!"}\n\n'
            else:
                yield 'data: {"error": "Lỗi trong quá trình chạy AI Agentic Crawler."}\n\n'
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
