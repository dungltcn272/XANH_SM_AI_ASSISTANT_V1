from __future__ import annotations

import io
import os
import sys
from pathlib import Path

from dotenv import dotenv_values
from pydantic_settings import BaseSettings, SettingsConfigDict


os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

for stream_name in ("stdout", "stderr"):
    stream = getattr(sys, stream_name)
    try:
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
        elif hasattr(stream, "buffer"):
            setattr(sys, stream_name, io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace"))
    except Exception:
        pass


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]
ROOT_ENV_FILE = PROJECT_ROOT / ".env"
BACKEND_ENV_FILE = BACKEND_ROOT / ".env"
ENV_FILE_OVERRIDE_KEYS = {
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "COHERE_API_KEY",
    "GOOGLE_CLIENT_ID",
    "EMBEDDING_PROVIDER",
    "EMBEDDING_MODEL",
    "RAG_ANSWER_MODEL",
    "NLU_MODEL",
    "FOOD_ANSWER_MODEL",
    "AI_JUDGE_MODEL",
    "VLM_MODEL",
    "RERANKER_PROVIDER",
    "RERANKER_MODEL",
    "OPENAI_TIMEOUT_SECONDS",
    "LLM_MAX_TOKENS",
}


def _load_env_files() -> None:
    for env_file in (ROOT_ENV_FILE, BACKEND_ENV_FILE):
        if not env_file.exists():
            continue
        for key, value in dotenv_values(env_file).items():
            if value is None:
                continue
            if key in os.environ and key not in ENV_FILE_OVERRIDE_KEYS:
                continue
            os.environ[key] = value


_load_env_files()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Xanh SM Modular AI Assistant"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/greensm_db")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-jwt-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
    RAG_ANSWER_MODEL: str = os.getenv("RAG_ANSWER_MODEL", "gpt-4o-mini")
    NLU_MODEL: str = os.getenv("NLU_MODEL", "gpt-4o-mini")
    FOOD_ANSWER_MODEL: str = os.getenv("FOOD_ANSWER_MODEL", "gpt-4o-mini")
    OPENAI_TIMEOUT_SECONDS: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1800"))
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "rerank-multilingual-v3.0")
    RETRIEVAL_CANDIDATE_LIMIT: int = int(os.getenv("RETRIEVAL_CANDIDATE_LIMIT", "25"))
    RERANK_TOP_N: int = int(os.getenv("RERANK_TOP_N", "10"))
    CONTEXT_EXPANSION_THRESHOLD: float = float(os.getenv("CONTEXT_EXPANSION_THRESHOLD", "0.7"))
    MAX_CHUNKS_PER_SECTION: int = int(os.getenv("MAX_CHUNKS_PER_SECTION", "10"))
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "400"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
    FOOD_SEARCH_RADIUS_KM: float = float(os.getenv("FOOD_SEARCH_RADIUS_KM", "8"))
    NOMINATIM_USER_AGENT: str = os.getenv("NOMINATIM_USER_AGENT", "xanhsm-modular-ai/1.0")
    OSRM_BASE_URL: str = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org")

    DATA_DIR: str = os.getenv("DATA_DIR", "./data")

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()
