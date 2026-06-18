import os
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import String, Text, case, or_
from app.db.database import get_db, Base
from app.db.models import RagRequestLog, User, Conversation, DocumentChunk, ErrorLog, CrawlSource, EvaluationRun, FoodCatalog
from app.core.config import settings
from app.food_recommendation.schemas import FoodRecommendationRequest
from app.food_recommendation.tool import recommend_food
from fastapi.responses import StreamingResponse
import asyncio
from typing import Optional

router = APIRouter()

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_FOOD_CATALOG_PATH = ROOT_DIR / "data" / "food_catalog" / "shopeefood_catalog.jsonl"

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


class FoodCatalogImportRequest(BaseModel):
    path: Optional[str] = None
    clear_existing: bool = False


def parse_optional_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def json_text(value) -> str:
    if value is None:
        return "[]"
    return json.dumps(value, ensure_ascii=False)


def resolve_repo_data_path(path_value: str | None) -> Path:
    candidate = Path(path_value) if path_value else DEFAULT_FOOD_CATALOG_PATH
    if not candidate.is_absolute():
        candidate = ROOT_DIR / candidate
    resolved = candidate.resolve()
    data_root = (ROOT_DIR / "data").resolve()
    if data_root not in resolved.parents and resolved != data_root:
        raise HTTPException(status_code=400, detail="Import path must stay inside data/")
    return resolved


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


@router.post("/food-catalog/import")
def import_food_catalog(req: FoodCatalogImportRequest = None, db: Session = Depends(get_db)):
    req = req or FoodCatalogImportRequest()
    catalog_path = resolve_repo_data_path(req.path)
    if not catalog_path.exists():
        raise HTTPException(status_code=404, detail=f"Food catalog JSONL not found: {catalog_path}")

    if req.clear_existing:
        db.query(FoodCatalog).delete()
        db.commit()

    inserted = 0
    updated = 0
    skipped = 0
    errors = []
    seen_sources = set()

    with catalog_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                skipped += 1
                errors.append({"line": line_number, "error": str(exc)})
                continue

            item_id = (row.get("item_id") or "").strip()
            name = (row.get("name") or row.get("merchant_name") or "").strip()
            if not item_id or not name:
                skipped += 1
                errors.append({"line": line_number, "error": "Missing item_id or name"})
                continue

            payload = {
                "item_id": item_id,
                "name": name,
                "description": row.get("description"),
                "category": row.get("category"),
                "cuisine": row.get("cuisine"),
                "taste_tags_json": json_text(row.get("taste_tags")),
                "diet_tags_json": json_text(row.get("diet_tags")),
                "ingredient_tags_json": json_text(row.get("ingredient_tags")),
                "price": row.get("price"),
                "discount_percent": row.get("discount_percent"),
                "final_price": row.get("final_price"),
                "currency": row.get("currency") or "VND",
                "image_url": row.get("image_url"),
                "merchant_id": row.get("merchant_id"),
                "merchant_name": row.get("merchant_name") or name,
                "merchant_rating": row.get("merchant_rating"),
                "merchant_review_count": row.get("merchant_review_count"),
                "merchant_address": row.get("merchant_address"),
                "merchant_lat": row.get("merchant_lat"),
                "merchant_lng": row.get("merchant_lng"),
                "merchant_open_hours_json": json_text(row.get("merchant_open_hours")),
                "avg_prep_minutes": row.get("avg_prep_minutes"),
                "base_delivery_fee": row.get("base_delivery_fee"),
                "fee_per_km": row.get("fee_per_km"),
                "service_radius_km": row.get("service_radius_km"),
                "source": row.get("source") or "shopeefood",
                "source_url": row.get("source_url"),
                "city": row.get("city"),
                "city_slug": row.get("city_slug"),
                "raw_ref": row.get("raw_ref"),
                "raw_json": json.dumps(row, ensure_ascii=False),
                "last_seen_at": parse_optional_datetime(row.get("last_seen_at")),
            }
            seen_sources.add(payload["source"])

            existing = db.query(FoodCatalog).filter(FoodCatalog.item_id == item_id).first()
            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                db.add(FoodCatalog(**payload))
                inserted += 1

    db.commit()
    total = db.query(FoodCatalog).count()
    return {
        "success": True,
        "path": str(catalog_path.relative_to(ROOT_DIR)),
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "total_food_catalog_rows": total,
        "sources": sorted(seen_sources),
        "errors": errors[:20],
    }


@router.post("/food-catalog/recommend")
def test_food_recommendation(req: FoodRecommendationRequest, db: Session = Depends(get_db)):
    items = recommend_food(
        lat=req.lat,
        lng=req.lng,
        category=req.category,
        taste_tags=req.taste_tags,
        budget_min=req.budget_min,
        budget_max=req.budget_max,
        meal_time=req.meal_time,
        max_distance_km=req.max_distance_km,
        user_id=req.user_id,
        limit=req.limit,
        db=db,
    )
    return {"success": True, "items": [item.model_dump() for item in items]}

@router.post("/ingest/crawl")
async def run_crawler(max_urls: int = 0):
    """
    Chạy Script Cào Dữ Liệu: Main Site, Platform/PDF, và VLM Image Processing. 
    Trả về stream SSE báo cáo tiến độ.
    """
    async def event_generator():
        import subprocess
        import sys
        import os
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
        env["TQDM_DISABLE"] = "1"

        # 1. Main Site Crawler
        yield 'data: {"step": "1/2 Bắt đầu Web Crawler (Main Site)..."}\n\n'
        try:
            cmd = [sys.executable, "-W", "ignore", "-u", "crawler/run_crawler.py", "--max-urls", str(max(0, max_urls))]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
            loop = asyncio.get_event_loop()
            
            def read_line():
                return process.stdout.readline()
            
            while True:
                line = await loop.run_in_executor(None, read_line)
                if not line: break
                line_str = line.decode('utf-8', errors='replace').strip()
                if line_str:
                    yield f'data: {{"step": {json.dumps(line_str, ensure_ascii=False)}}}\n\n'
                    await asyncio.sleep(0.01)
                    
            process.wait()
            if process.returncode != 0:
                yield 'data: {"error": "Lỗi trong quá trình cào dữ liệu Main Site."}\n\n'
        except Exception as e:
            yield f'data: {{"error": "Lỗi cào Main Site: {str(e)}"}}\n\n'

        # 2. Platform / PDF Crawler
        yield 'data: {"step": "2/2 Bắt đầu Platform/PDF Crawler..."}\n\n'
        try:
            cmd = [sys.executable, "-W", "ignore", "-u", "crawler/agent_crawler.py", "--sources", "platform,platform_pdf", "--max-urls", str(max(0, max_urls))]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
            loop = asyncio.get_event_loop()
            
            def read_line():
                return process.stdout.readline()
            
            while True:
                line = await loop.run_in_executor(None, read_line)
                if not line: break
                line_str = line.decode('utf-8', errors='replace').strip()
                if line_str:
                    if "[AGENT_STEP]" in line_str:
                        step_part = line_str.split("[AGENT_STEP]")[-1].strip()
                        yield f'data: {{"step": "[AGENT_STEP] {step_part}"}}\n\n'
                    else:
                        yield f'data: {{"step": {json.dumps(line_str, ensure_ascii=False)}}}\n\n'
                    await asyncio.sleep(0.01)
                    
            process.wait()
            if process.returncode != 0:
                yield 'data: {"error": "Lỗi trong quá trình cào Platform/PDF."}\n\n'
        except Exception as e:
            yield f'data: {{"error": "Lỗi cào Platform/PDF: {str(e)}"}}\n\n'
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

import queue

import queue
@router.post("/ingest/process/vlm")
async def run_vlm_processor():
    """
    Chạy VLM Process cho hình ảnh trong data/news. Trả về stream SSE báo cáo tiến độ.
    """
    async def event_generator():
        yield 'data: {"step": "Bắt đầu tiền xử lý hình ảnh bằng VLM cho data/news..."}\n\n'
        import os
        import asyncio
        from app.ingestion.process_images import process_markdown_images_in_directory
        
        q = queue.Queue()
        def log_cb(msg: str):
            q.put(msg)
            
        loop = asyncio.get_event_loop()
        # knowledge.py is in app/api/admin/ -> 4 levels up to get to root
        news_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "news")
        
        def run_vlm():
            process_markdown_images_in_directory(news_dir, log_callback=log_cb)
            q.put(None) # EOF marker
            
        task = loop.run_in_executor(None, run_vlm)
        
        while True:
            # wait for messages
            msg = await loop.run_in_executor(None, q.get)
            if msg is None:
                break
            yield f'data: {{"step": {json.dumps(msg, ensure_ascii=False)}}}\n\n'
            
        await task
        yield 'data: {"step": "Xử lý hình ảnh VLM hoàn tất!"}\n\n'
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


