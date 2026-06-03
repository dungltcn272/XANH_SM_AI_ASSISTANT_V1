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

    return {
        "total_users": total_users,
        "total_requests": total_requests,
        "total_conversations": total_conversations,
        "total_blocked": total_blocked,
        "avg_latency": avg_latency / 1000.0  # Convert ms to s for UI
    }

@router.get("/eval")
def get_eval_results():
    try:
        with open("evaluation_report.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Evaluation report not found. Please run the benchmark first."}

@router.get("/logs")
def get_rag_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(RagRequestLog).order_by(RagRequestLog.created_at.desc()).limit(limit).all()
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
def get_table_data(table_name: str, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    metadata = Base.metadata
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail="Table not found")
        
    table = metadata.tables[table_name]
    
    # Get total count
    total = db.query(func.count()).select_from(table).scalar()
    
    # Get rows
    rows = db.query(table).offset(offset).limit(limit).all()
    # Convert Row objects to dicts using ._mapping to handle named tuples in SQLAlchemy 2.0+
    data = [dict(row._mapping) for row in rows]
    
    return {
        "total": total,
        "data": data,
        "columns": [c.name for c in table.columns]
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
