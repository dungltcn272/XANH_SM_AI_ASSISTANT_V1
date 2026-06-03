import os
import sys
import io

# Prevent OpenMP crash on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

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

app = FastAPI(
    title="GreenSM Production RAG",
    description="Xanh SM Enterprise Production RAG System (Phase 5)",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
