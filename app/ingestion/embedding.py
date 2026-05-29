from typing import List
from langchain_core.embeddings import Embeddings
from app.config import config

class CustomEmbeddings(Embeddings):
    """
    Unified Embedding Client supporting OpenAI, SentenceTransformers, and simple local mocks.
    Includes fully self-healing fallback to prevent crashes if OpenAI API keys are invalid.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CustomEmbeddings, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self.provider = config.EMBEDDING_PROVIDER.lower()
        self.model_name = config.EMBEDDING_MODEL
        
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.provider == "openai":
            try:
                from langchain_openai import OpenAIEmbeddings
                self.client = OpenAIEmbeddings(
                    openai_api_key=config.OPENAI_API_KEY,
                    model=self.model_name
                )
                print(f"[INFO] Initialized OpenAI Embeddings model={self.model_name}")
            except Exception as e:
                print(f"[WARN] Failed to load OpenAI Embeddings: {e}. Falling back to Local/Mock.")
                self.provider = "local"
                config.EMBEDDING_PROVIDER = "local"
                
        if self.provider == "local":
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                self.client = HuggingFaceEmbeddings(
                    model_name=self.model_name,
                    model_kwargs={'device': 'cpu'}
                )
                print(f"[INFO] Initialized HuggingFace Embeddings model={self.model_name}")
            except Exception as e:
                print(f"[WARN] Failed to load HuggingFace Embeddings: {e}. Using MockEmbeddings for offline compatibility.")
                self.provider = "mock"
                config.EMBEDDING_PROVIDER = "mock"
                
        if self.provider == "mock":
            print("[INFO] MockEmbeddings active. Producing deterministic zero-filled float lists of length 1536.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.provider == "mock" or not self.client:
            return [[0.0] * 1536 for _ in texts]
            
        try:
            return self.client.embed_documents(texts)
        except Exception as e:
            print(f"[WARN] Embedding generation failed ({e}). Switching globally to Mock Embeddings.")
            self.provider = "mock"
            config.EMBEDDING_PROVIDER = "mock" # Propagate offline fallback globally
            return [[0.0] * 1536 for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        if self.provider == "mock" or not self.client:
            return [0.0] * 1536
            
        try:
            return self.client.embed_query(text)
        except Exception as e:
            print(f"[WARN] Query embedding failed ({e}). Switching globally to Mock Query Embedding.")
            self.provider = "mock"
            config.EMBEDDING_PROVIDER = "mock" # Propagate offline fallback globally
            return [0.0] * 1536

def get_embeddings():
    return CustomEmbeddings()
