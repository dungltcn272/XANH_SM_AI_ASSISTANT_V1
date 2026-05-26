import os
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv(override=True)

class RAGConfig:
    # General API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Embedding Configuration
    # Options: "openai", "local", or "mock" (Defaults to "mock" for out-of-the-box offline stability)
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "mock")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # VectorDB Configuration
    # Options: "chromadb" or "fallback" (In-Memory Fallback to avoid native C++ SQLite crashes on Windows host)
    CHROMA_PROVIDER: str = os.getenv("CHROMA_PROVIDER", "fallback")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "xanh_sm_rag")
    
    # Reranker Configuration
    # Options: "local" (BAAI/bge-reranker-v2-m3) or "cohere" or "none"
    RERANKER_PROVIDER: str = os.getenv("RERANKER_PROVIDER", "none")
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
    
    # Crawler Configuration
    MAX_CRAWL_DEPTH: int = int(os.getenv("MAX_CRAWL_DEPTH", "3"))
    MAX_CRAWL_PAGES: int = int(os.getenv("MAX_CRAWL_PAGES", "100"))
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # Path mappings
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")

# Fallback values adjustments
config = RAGConfig()

# If user has not pasted API key yet, automatically run offline mock/heuristic mode
if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
    config.EMBEDDING_PROVIDER = "mock"
    config.RERANKER_PROVIDER = "none"
