import os
import sys
import io
import asyncio

# Set TIKTOKEN_CACHE_DIR for offline mode
if "TIKTOKEN_CACHE_DIR" not in os.environ:
    os.environ["TIKTOKEN_CACHE_DIR"] = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "tiktoken_cache"
    )

# Prevent OpenMP crash on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Force WindowsProactorEventLoopPolicy to support asyncio subprocesses
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Force UTF-8 encoding for all stdout/stderr on Windows
# This MUST be done before any other imports to prevent UnicodeEncodeError
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    else:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

try:
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    else:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, chat, admin, conversations
from app.db.database import engine, Base

# Tạo các bảng trong CSDL
Base.metadata.create_all(bind=engine)

# Chạy ALTER TABLE động để thêm các cột latency mới vào bảng rag_request_logs nếu chưa tồn tại
from sqlalchemy import text
with engine.connect() as conn:
    for col in ["rewrite_latency_ms", "classification_latency_ms", "expansion_latency_ms", "rerank_latency_ms"]:
        try:
            conn.execute(text(f"ALTER TABLE rag_request_logs ADD COLUMN {col} FLOAT DEFAULT 0;"))
            conn.commit()
        except Exception:
            pass

app = FastAPI(
    title="GreenSM Production RAG",
    description="Xanh SM Enterprise Production RAG System (Phase 4)",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex="https://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
def root():
    return {"message": "Welcome to Xanh SM RAG API v4 (Production Phase 4)"}
