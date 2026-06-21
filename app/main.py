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
from app.api import auth, chat, conversations, reviews, food, notifications
from app.api.admin import router as admin_router

app = FastAPI(
    title="GreenSM Production RAG",
    description="Xanh SM Enterprise Production RAG System (Phase 9)",
    version="9.0.0"
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
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(food.router, prefix="/api/food", tags=["food"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(admin_router, prefix="/api/admin")

@app.get("/")
def root():
    return {"message": "Welcome to Xanh SM RAG API v4 (Production Phase 4)"}
