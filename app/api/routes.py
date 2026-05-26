import os
from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.rag.chain import XanhSMRAGPipeline
from app.ingestion.ingest import run_ingestion
from app.crawler.crawl import GreenSMCrawler
from app.retrieval.hybrid_search import XanhSMHybridSearch
from app.config import config

app = FastAPI(
    title="Xanh SM Production RAG API",
    description="Advanced Enterprise RAG System for Xanh SM Customers, Drivers, Merchants, and CSKH Agents.",
    version="1.0.0"
)

# API schemas
class ChatRequest(BaseModel):
    query: str = Field(..., example="Hoa hồng tài xế Xanh Car là bao nhiêu?")
    role: Optional[str] = Field("faq", example="driver", description="customer, driver, merchant, agent, faq")

class CitationSchema(BaseModel):
    source: str
    section: str
    url: str
    relevance_score: float

class ChatResponse(BaseModel):
    query: str
    role: str
    answer: str
    citations: List[CitationSchema]

class CrawlRequest(BaseModel):
    url: str = Field("https://www.greensm.com/vn-vi/terms-policies", example="https://www.greensm.com/vn-vi/terms-policies")
    max_depth: Optional[int] = Field(2, ge=1, le=5)
    max_pages: Optional[int] = Field(20, ge=1, le=100)

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

@app.post("/api/chat", response_model=ChatResponse)
def api_chat(request: ChatRequest):
    """
    Chat endpoint for Xanh SM RAG.
    Applies role pre-filtering, query expansion, dense + sparse retrieval, reranking, and citation generation.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        rag = get_pipeline()
        result = rag.run(query=request.query, role=request.role)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        background_tasks.add_task(run_ingestion)
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
        run_ingestion()

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
