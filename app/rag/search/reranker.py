import time
from typing import List
from langchain_core.documents import Document
from app.core.config import settings as config
from app.core.logger import log_info, log_warn

# Global cache for reranker models to prevent reloading
_MODEL_CACHE = {}

class XanhSMReranker:
    """
    Advanced Reranker using Cohere (Cloud-based Enterprise).
    """
    
    def __init__(self, provider: str = "cohere", model_name: str = None):
        self.provider = "cohere"
        self.model_name = model_name or config.RERANKER_MODEL or "rerank-multilingual-v3.0"
        self.model = None
        
        cache_key = f"{self.provider}:{self.model_name}"
        if cache_key in _MODEL_CACHE:
            self.model = _MODEL_CACHE[cache_key]
            return

        try:
            import cohere
            api_key = getattr(config, "COHERE_API_KEY", None)
            if not api_key:
                raise ValueError("COHERE_API_KEY is missing in config.")
            self.model = cohere.Client(api_key)
            _MODEL_CACHE[cache_key] = self.model
            log_info("RERANK", f"Initialized Cohere Rerank: {self.model_name}")
        except Exception as e:
            log_warn("RERANK", f"Cohere initialization failed: {e}")

    def rerank(self, query: str, docs: List[Document], top_n: int = 5) -> List[Document]:
        if not docs: return []
        if not self.model:
            log_warn("RERANK", "Reranker model not initialized. Returning original docs.")
            return docs[:top_n]
        
        start_time = time.time()
        
        try:
            texts = [doc.page_content for doc in docs]
            results = self.model.rerank(
                query=query, 
                documents=texts, 
                top_n=top_n, 
                model=self.model_name
            )
            
            sorted_docs = []
            for res in results.results:
                doc = docs[res.index]
                doc.metadata["rerank_score"] = float(res.relevance_score)
                sorted_docs.append(doc)
            
            elapsed = (time.time() - start_time) * 1000
            log_info("RERANK", f"Cohere rerank took {elapsed:.2f}ms")
            return sorted_docs
        except Exception as e:
            log_warn("RERANK", f"Reranking failed: {e}. Returning original docs.")
            return docs[:top_n]

