import os
import sys
import io
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# ────────────────────────────────────────────────────────────────
# Force UTF-8 stdout/stderr on Windows to prevent UnicodeEncodeError
# when printing Vietnamese characters. This runs before any other
# module to ensure all subsequent print() calls are safe.
# ────────────────────────────────────────────────────────────────
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    elif hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

try:
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    elif hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass


load_dotenv(override=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = "GreenSM Production RAG"
    
    # DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/greensm_db")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    
    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-jwt-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    
    # LLM & Embedding
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    NLU_MODEL: str = os.getenv("NLU_MODEL", "gpt-4o-mini")
    AI_JUDGE_MODEL: str = os.getenv("AI_JUDGE_MODEL", "gpt-4o-mini")
    OPENAI_TIMEOUT_SECONDS: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "900"))
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "openai")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    NLU_FAST_PATH_ENABLED: bool = os.getenv("NLU_FAST_PATH_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    NLU_FAST_PATH_MIN_CHARS: int = int(os.getenv("NLU_FAST_PATH_MIN_CHARS", "28"))

    # Retrieval tuning
    RETRIEVAL_CANDIDATE_LIMIT: int = int(os.getenv("RETRIEVAL_CANDIDATE_LIMIT", "25"))
    RERANK_TOP_N: int = int(os.getenv("RERANK_TOP_N", "8"))
    CONTEXT_EXPANSION_THRESHOLD: float = float(os.getenv("CONTEXT_EXPANSION_THRESHOLD", "0.65"))
    MAX_CHUNKS_PER_SECTION: int = int(os.getenv("MAX_CHUNKS_PER_SECTION", "10"))
    
    # Reranker
    RERANKER_PROVIDER: str = os.getenv("RERANKER_PROVIDER", "cohere")
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "rerank-v3.0")
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
    
    # Crawl / Data
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
