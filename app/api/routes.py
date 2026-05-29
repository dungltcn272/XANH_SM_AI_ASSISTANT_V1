import os
import sys

# Force UTF-8 encoding on standard streams to prevent CP1252 console encoding crashes on Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.rag.chain import XanhSMRAGPipeline
from app.ingestion.ingest import run_ingestion
from app.crawler.crawl import GreenSMCrawler
from app.retrieval.hybrid_search import XanhSMHybridSearch
from app.config import config
import threading
import os

app = FastAPI(
    title="Xanh SM Production RAG API",
    description="Advanced Enterprise RAG System for Xanh SM Customers, Drivers, Merchants, and CSKH Agents.",
    version="1.0.0"
)

# API schemas
class ChatRequest(BaseModel):
    query: str = Field(..., example="Hoa hồng tài xế Xanh Car là bao nhiêu?")
    role: Optional[str] = Field("faq", example="driver", description="customer, driver, merchant, agent, faq")
    chat_history: Optional[List[Dict[str, str]]] = Field(None, description="Previous message turns")
    image_base64: Optional[str] = Field(None, description="Base64 encoded string of image uploader")
    image_mime_type: Optional[str] = Field(None, description="Mime type of uploaded image (e.g. image/png)")

class CitationSchema(BaseModel):
    source: str
    section: str
    url: str
    relevance_score: float

class ChatResponse(BaseModel):
    query: str
    rewritten_query: Optional[str] = None
    role: str
    answer: str
    citations: List[CitationSchema]
    cache_hit: Optional[str] = None
    cache_similarity: Optional[float] = None
    llm_cost_usd: Optional[float] = None
    llm_cost_vnd: Optional[float] = None
    token_usage: Optional[Dict[str, Any]] = None
    compressed_context_len: Optional[int] = None
    intent: Optional[str] = None
    gateway_checked: Optional[bool] = None
    strategy_selected: Optional[str] = None
    faithfulness_passed: Optional[bool] = None
    missing_fields: Optional[bool] = None



class CrawlRequest(BaseModel):
    url: str = Field("https://www.greensm.com/vn-vi/terms-policies", example="https://www.greensm.com/vn-vi/terms-policies")
    max_depth: Optional[int] = Field(2, ge=1, le=5)
    max_pages: Optional[int] = Field(20, ge=1, le=100)

class EvaluateRequest(BaseModel):
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key to override default key")

class IngestResponse(BaseModel):
    status: str
    message: str

# Lazy load pipeline to speed up start times
pipeline = None
hybrid_search = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        pipeline = XanhSMRAGPipeline()
    return pipeline

def get_hybrid_search():
    global hybrid_search
    if hybrid_search is None:
        hybrid_search = XanhSMHybridSearch()
    return hybrid_search

def reset_pipeline_singleton():
    global pipeline, hybrid_search
    pipeline = None
    hybrid_search = None
    print("[INFO] Global singletons reset: pipeline and hybrid_search set to None.")

def run_ingestion_and_reset():
    try:
        run_ingestion()
        reset_pipeline_singleton()
    except Exception as e:
        print(f"[ERROR] run_ingestion_and_reset background task failed: {e}")



@app.on_event("startup")
def startup_auto_ingest():
    try:
        chroma_dir = os.path.abspath(config.CHROMA_PERSIST_DIR)
        marker_file = os.path.join(chroma_dir, ".ingestion_done")
        data_dir = os.path.abspath(config.DATA_DIR)

        def _has_markdown(dir_path):
            return os.path.isdir(dir_path) and any(
                fname.endswith('.md') for _, _, files in os.walk(dir_path) for fname in files
            )

        if os.path.exists(marker_file):
            print(f"[INFO] Ingestion marker found at {marker_file}; skipping auto-ingest.")
            return

        repo_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        if not _has_markdown(data_dir) and not _has_markdown(repo_data_dir):
            print("[INFO] No markdown data found in DATA_DIR or bundled repo data; skipping auto-ingest.")
            return

        def _bg_ingest():
            try:
                print("[INFO] Auto-ingest starting in background thread...")
                run_ingestion()
                os.makedirs(chroma_dir, exist_ok=True)
                with open(marker_file, "w", encoding="utf-8") as f:
                    f.write("done")
                print("[INFO] Auto-ingest completed; marker written.")
            except Exception as e:
                print(f"[WARN] Auto-ingest failed: {e}")

        t = threading.Thread(target=_bg_ingest, daemon=True)
        t.start()
    except Exception as e:
        print(f"[WARN] Error during startup auto-ingest check: {e}")

@app.post("/api/chat", response_model=ChatResponse)
def api_chat(request: ChatRequest):
    """
    Chat endpoint for Xanh SM RAG.
    Applies safety gateway, intent classification, slot filling, strategic search, and faithfulness verification.
    Supports chat history query rewriting and image warning lights vision diagnostics.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        import base64
        rag = get_pipeline()
        
        # 1. Image logic (Currently restricted to basic upload logs)
        actual_query = request.query
        if request.image_base64:
            print("[INFO] Image uploaded, but Vision AI diagnostics are currently disabled per UI policy.")
            # We skip run_vision_diagnostics and just use the raw text query

                
        # 2. Run NLU-Gateway RAG Pipeline
        result = rag.run(query=actual_query, role=request.role, chat_history=request.chat_history)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
def api_chat_stream(request: ChatRequest):
    """
    Server-Sent Events (SSE) streaming endpoint for real-time pipeline visualization.
    Streams pipeline stages as they execute, enabling real-time animation on the frontend.
    """
    import json
    from fastapi.responses import StreamingResponse
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    def event_generator():
        try:
            rag = get_pipeline()
            
            # Handle vision input (Disabled)
            actual_query = request.query
            if request.image_base64:
                print("[INFO] Image uploaded (stream), but Vision AI diagnostics are currently disabled.")

            
            # Stream each stage from the generator
            for stage_event in rag.run_step_by_step(query=actual_query, role=request.role, chat_history=request.chat_history):
                stage_name = stage_event.get("stage", "Unknown")
                msg = stage_event.get("msg", "")
                result = stage_event.get("result", None)
                
                event_data = {
                    "stage": stage_name,
                    "msg": msg,
                    "result": result
                }
                
                # Yield SSE formatted data
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_data = {
                "stage": "Error",
                "msg": str(e),
                "result": None
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@app.get("/api/search")
def api_search(query: str, role: Optional[str] = "faq", limit: Optional[int] = 10):
    """
    Developer debug endpoint to verify Hybrid Search & RRF score list.
    """
    try:
        searcher = get_hybrid_search()
        results = searcher.search(query=query, role=role, limit=limit)
        
        serializable_results = []
        for doc in results:
            serializable_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
        return {"query": query, "role": role, "results": serializable_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest", response_model=IngestResponse)
def api_ingest(background_tasks: BackgroundTasks):
    """
    Triggers re-indexing of all documents inside the data/ folder.
    """
    try:
        background_tasks.add_task(run_ingestion_and_reset)
        return {"status": "success", "message": "Document ingestion started in the background."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawl")
def api_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """
    Launches BFS crawler in the background.
    """
    def run_crawler_bg():
        crawler = GreenSMCrawler(start_url=request.url, max_depth=request.max_depth, max_pages=request.max_pages)
        crawler.crawl()
        # Automatically run ingestion after crawl finishes
        run_ingestion_and_reset()

    try:
        background_tasks.add_task(run_crawler_bg)
        return {"status": "success", "message": f"BFS Crawler started in background for {request.url}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def api_health():
    return {"status": "healthy", "config": {
        "embedding_provider": config.EMBEDDING_PROVIDER,
        "chroma_dir": config.CHROMA_PERSIST_DIR,
        "llm_model": config.LLM_MODEL
    }}

@app.post("/api/cache/clear")
def clear_cache():
    try:
        from app.rag.cache import XanhSMRAGCache
        cache = XanhSMRAGCache()
        cache.clear()
        return {"status": "success", "message": "Successfully cleared RAG Cache Database."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evaluate")
def api_evaluate(request: Optional[EvaluateRequest] = None):
    """
    Runs the automated RAGAS quality evaluation suite.
    """
    try:
        from app.evaluation.ragas_eval import XanhSMEvaluation
        if request and request.openai_api_key and request.openai_api_key.strip():
            from app.config import config
            config.OPENAI_API_KEY = request.openai_api_key.strip()
            config.EMBEDDING_PROVIDER = "openai"
            # Reset pipeline to force reload with new config
            global pipeline
            pipeline = None
            
        evaluator = XanhSMEvaluation()
        report = evaluator.run_suite()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluate/dataset")
def get_evaluation_dataset():
    try:
        import json
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evaluation", "golden_dataset.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                dataset = json.load(f)
            return {"status": "success", "count": len(dataset), "dataset": dataset}
        else:
            from app.evaluation.golden_dataset import GOLDEN_DATASET
            return {"status": "success", "count": len(GOLDEN_DATASET), "dataset": GOLDEN_DATASET}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/db/stats")

def db_stats():
    try:
        from app.vectordb.chroma_client import XanhSMVectorDB
        from app.rag.cache import XanhSMRAGCache
        
        chroma_count = 0
        is_fallback = True
        chroma_active = False
        try:
            db = XanhSMVectorDB()
            if db._vector_store == "fallback":
                chroma_count = len(db._fallback_docs)
                chroma_active = False
            elif db._vector_store is not None:
                chroma_count = db._vector_store._collection.count()
                is_fallback = False
                chroma_active = True
        except Exception as e:
            print(f"[WARN] Failed to get Chroma count: {e}")
            
        cache_count = 0
        driver = "SQLite"
        cache_active = False
        try:
            cache = XanhSMRAGCache()
            driver = "PostgreSQL" if cache.use_postgres else "SQLite"
            conn = cache._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM rag_cache")
            cache_count = cursor.fetchone()[0]
            conn.close()
            cache_active = True
        except Exception as e:
            print(f"[WARN] Failed to get cache count: {e}")
            
        return {
            "chroma_count": chroma_count,
            "is_fallback": is_fallback,
            "chroma_active": chroma_active,
            "cache_count": cache_count,
            "cache_driver": driver,
            "cache_active": cache_active
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/files")
def get_data_files():
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        files_list = []
        if os.path.exists(data_dir):
            for root, _, files in os.walk(data_dir):
                for file in files:
                    if file.endswith(".md") or file.endswith(".txt"):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, data_dir).replace("\\", "/")
                        size_bytes = os.path.getsize(full_path)
                        parts = rel_path.split("/")
                        role = parts[0] if len(parts) > 1 else "faq"
                        files_list.append({
                            "path": rel_path,
                            "name": file,
                            "size_bytes": size_bytes,
                            "role": role
                        })
        return {"status": "success", "files": files_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/file")
def get_data_file(path: str):
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        safe_path = os.path.abspath(os.path.join(data_dir, path))
        if not safe_path.startswith(os.path.abspath(data_dir)):
            raise HTTPException(status_code=403, detail="Access denied.")
            
        if not os.path.exists(safe_path):
            raise HTTPException(status_code=404, detail="File not found.")
            
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return {"status": "success", "path": path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import UploadFile, File, Form

@app.post("/api/simulate/chunk")
async def simulate_chunk(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    try:
        content = ""
        filename = "simulated_doc.md"
        if file:
            filename = file.filename
            file_bytes = await file.read()
            if filename.lower().endswith(".pdf"):
                import pypdf
                import io
                pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text_list = []
                for page in pdf_reader.pages:
                    txt = page.extract_text()
                    if txt:
                        text_list.append(txt)
                content = "\n".join(text_list)
                if not any(content.strip().startswith(h) for h in ["#", "##", "###"]):
                    content = f"# {filename.replace('.pdf', '').replace('.PDF', '')}\n\n" + content
            else:
                content = file_bytes.decode("utf-8", errors="ignore")
        elif text:
            content = text
        else:
            raise HTTPException(status_code=400, detail="No text or file provided.")
            
        from app.ingestion.splitter import HeadingAwareSplitter
        splitter = HeadingAwareSplitter()
        
        frontmatter_meta, body = splitter.parse_frontmatter(content)
        header_docs = splitter.markdown_splitter.split_text(body)
        
        chunks = []
        import hashlib
        for doc in header_docs:
            parent_content = doc.page_content.strip()
            parent_chunk_id = hashlib.md5(parent_content.encode('utf-8')).hexdigest()
            
            sub_docs = splitter.recursive_splitter.split_documents([doc])
            for idx, sub_doc in enumerate(sub_docs):
                headers = []
                if "Header 1" in sub_doc.metadata:
                    headers.append(sub_doc.metadata["Header 1"])
                if "Header 2" in sub_doc.metadata:
                    headers.append(sub_doc.metadata["Header 2"])
                if "Header 3" in sub_doc.metadata:
                    headers.append(sub_doc.metadata["Header 3"])
                
                section = " > ".join(headers) if headers else "Introduction"
                unique_str = f"{filename}_{section}_{idx}"
                chunk_id = hashlib.md5(unique_str.encode('utf-8')).hexdigest()
                
                chunks.append({
                    "chunk_id": chunk_id,
                    "parent_chunk_id": parent_chunk_id,
                    "parent_content": parent_content[:150] + "..." if len(parent_content) > 150 else parent_content,
                    "page_content": sub_doc.page_content,
                    "section": section,
                    "size_chars": len(sub_doc.page_content)
                })
                
        return {
            "status": "success",
            "filename": filename,
            "frontmatter": frontmatter_meta,
            "preprocessed_chars": len(body),
            "chunks_count": len(chunks),
            "chunks": chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class EmbedRequest(BaseModel):
    texts: List[str]

@app.post("/api/rerank/arena")
def run_reranker_arena(request: ChatRequest):
    """
    Live Reranker Arena: Compares multiple reranking strategies on a real query.
    """
    try:
        from app.rag.chain import XanhSMRAGPipeline
        from app.retrieval.reranker import XanhSMReranker
        import time

        pipeline = XanhSMRAGPipeline()
        query = request.query
        
        # 1. Retrieval
        candidates = pipeline.search_engine.search(query=query, limit=25, role=request.role or "customer")
        
        # 2. Define Models to Test (Align with FE table names exactly)
        test_configs = [
            {"name": "Heuristic Semantic (Current)", "provider": "heuristic", "model": None},
            {"name": "MiniLM CrossEncoder", "provider": "local", "model": "cross-encoder/ms-marco-MiniLM-L-6-v2"},
            {"name": "FlashRank", "provider": "flashrank", "model": "ms-marco-MiniLM-L-12-v2"},
            {"name": "BGE-reranker-base", "provider": "local", "model": "BAAI/bge-reranker-base"},
            {"name": "Cohere Rerank", "provider": "cohere", "model": "rerank-v3.0"},
            {"name": "MonoT5", "provider": "local", "model": "castorini/monot5-base-msmarco-10k"}
        ]
        
        arena_results = []
        for cfg in test_configs:
            try:
                rk = XanhSMReranker(provider=cfg['provider'], model_name=cfg['model'])
                start = time.time()
                top_docs = rk.rerank(query, candidates, top_n=3)
                duration = (time.time() - start) * 1000
                
                # Report if a fallback occurred to help user understand the speed
                display_speed = f"{duration:.1f}ms"
                if rk.fallback_occurred:
                    display_speed += " (Fallback)"

                arena_results.append({
                    "model": cfg['name'],
                    "speed": display_speed,
                    "top_chunks": [
                        {
                            "source": doc.metadata.get("source", "N/A"),
                            "score": round(doc.metadata.get("rerank_score", 0), 4),
                            "content": doc.page_content[:200] + "..."
                        } for doc in top_docs
                    ]
                })
            except Exception as e:
                arena_results.append({"model": cfg['name'], "error": str(e)})

        return {"status": "success", "results": arena_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulate/embed")
def simulate_embed(request: EmbedRequest):
    try:
        import random
        embeddings = []
        for text in request.texts:
            import hashlib
            h = hashlib.md5(text.encode("utf-8")).hexdigest()
            random.seed(int(h, 16) % 1000000)
            sample_vector = [round(random.uniform(-0.5, 0.5), 4) for _ in range(8)]
            embeddings.append({
                "sample_vector": sample_vector,
                "dimension": 1536,
                "text_snippet": text[:40] + "..." if len(text) > 40 else text
            })
        return {"status": "success", "embeddings": embeddings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount standalone premium Front-End static directory Served directly by FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

fe_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "FE")
if os.path.exists(fe_path):
    print(f"[OK] Mount Static Front-End folder from: {fe_path}")
    app.mount("/FE", StaticFiles(directory=fe_path, html=True), name="FE")
    
    @app.get("/")
    def redirect_to_fe():
        return RedirectResponse(url="/FE/")
else:
    print(f"[WARN] FE static directory not found at: {fe_path}")

