import time
import unicodedata
from typing import List, Dict, Any
from langchain_core.documents import Document
from app.config import config

# Global cache for reranker models to prevent reloading
_MODEL_CACHE = {}

class XanhSMReranker:
    """
    Advanced Reranker supporting multiple providers:
    - local (MiniLM, BGE, MonoT5 via SentenceTransformers)
    - flashrank (Ultra-fast ONNX)
    - cohere (Cloud-based Enterprise)
    - heuristic (Fast keyword matching fallback)
    """
    
    def __init__(self, provider: str = None, model_name: str = None):
        self.requested_provider = (provider or config.RERANKER_PROVIDER or "heuristic").lower()
        self.provider = self.requested_provider
        self.model_name = model_name or config.RERANKER_MODEL
        self.model = None
        self.fallback_occurred = False
        
        cache_key = f"{self.provider}:{self.model_name}"
        if cache_key in _MODEL_CACHE:
            self.model = _MODEL_CACHE[cache_key]
            return

        # 1. FlashRank (Ultra Fast)
        if self.provider == "flashrank":
            try:
                from flashrank import Ranker
                self.model = Ranker(model_name=self.model_name or "ms-marco-MiniLM-L-12-v2", cache_dir="/tmp")
                _MODEL_CACHE[cache_key] = self.model
                print(f"[+] Initialized FlashRank: {self.model_name or 'ms-marco-MiniLM-L-12-v2'}")
            except Exception as e:
                print(f"[!] FlashRank failed: {e}. Falling back to heuristic.")
                self.provider = "heuristic"
                self.fallback_occurred = True

        # 2. Local Cross-Encoders (MiniLM, BGE, MonoT5)
        elif self.provider == "local":
            try:
                from sentence_transformers import CrossEncoder
                m_name = self.model_name or "cross-encoder/ms-marco-MiniLM-L-6-v2"
                
                # Special handling for MonoT5 as it's not a standard CrossEncoder
                if "monot5" in m_name.lower():
                    m_name = "cross-encoder/ms-marco-en-electra-base" 
                    print(f"[INFO] MonoT5 redirected to ELECTRA Cross-Encoder for compatibility: {m_name}")
                
                self.model = CrossEncoder(m_name, max_length=512)
                _MODEL_CACHE[cache_key] = self.model
                print(f"[+] Initialized Local Cross-Encoder: {m_name}")
            except Exception as e:
                print(f"[!] Local CrossEncoder failed: {e}. Falling back to heuristic.")
                self.provider = "heuristic"
                self.fallback_occurred = True

        # 3. Cohere (Cloud) - API Client is lightweight, but we can still cache it
        elif self.provider == "cohere":
            try:
                import cohere
                api_key = getattr(config, "COHERE_API_KEY", None)
                if not api_key:
                    raise ValueError("COHERE_API_KEY is missing in config.")
                self.model = cohere.Client(api_key)
                _MODEL_CACHE[cache_key] = self.model
                print(f"[+] Initialized Cohere Rerank: {self.model_name or 'rerank-v3.0'}")
            except Exception as e:
                print(f"[!] Cohere failed: {e}. Falling back to heuristic.")
                self.provider = "heuristic"
                self.fallback_occurred = True

    def rerank(self, query: str, docs: List[Document], top_n: int = 5) -> List[Document]:
        if not docs: return []
        
        start_time = time.time()
        
        # FLASH RANK
        if self.provider == "flashrank" and self.model:
            from flashrank import RerankRequest
            passages = [{"id": i, "text": doc.page_content} for i, doc in enumerate(docs)]
            rank_request = RerankRequest(query=query, passages=passages)
            results = self.model.rerank(rank_request)
            
            sorted_docs = []
            for res in results[:top_n]:
                doc = docs[res['id']]
                doc.metadata["rerank_score"] = float(res['score'])
                sorted_docs.append(doc)
            self._log_time(start_time)
            return sorted_docs

        # LOCAL CROSS-ENCODER
        elif self.provider == "local" and self.model:
            pairs = [[query, doc.page_content] for doc in docs]
            scores = self.model.predict(pairs)
            for idx, score in enumerate(scores):
                docs[idx].metadata["rerank_score"] = float(score)
            sorted_docs = sorted(docs, key=lambda x: x.metadata["rerank_score"], reverse=True)
            self._log_time(start_time)
            return sorted_docs[:top_n]

        # COHERE
        elif self.provider == "cohere" and self.model:
            texts = [doc.page_content for doc in docs]
            results = self.model.rerank(
                query=query, 
                documents=texts, 
                top_n=top_n, 
                model=self.model_name or "rerank-v3.0"
            )
            sorted_docs = []
            for res in results.results:
                doc = docs[res.index]
                doc.metadata["rerank_score"] = float(res.relevance_score)
                sorted_docs.append(doc)
            self._log_time(start_time)
            return sorted_docs

        # HEURISTIC FALLBACK
        return self._heuristic_rerank(query, docs, top_n, start_time)

    def _heuristic_rerank(self, query: str, docs: List[Document], top_n: int, start_time: float) -> List[Document]:
        def clean_text(text: str) -> str:
            text = text.lower()
            normalized = unicodedata.normalize('NFKD', text)
            no_accents = ''.join([c for c in normalized if not unicodedata.combining(c)])
            return no_accents.replace('đ', 'd')

        clean_query = clean_text(query)
        query_words = set(clean_query.split())
        for doc in docs:
            clean_doc = clean_text(doc.page_content)
            doc_words = clean_doc.split()
            match_count = sum(1 for word in query_words if word in doc_words)
            doc.metadata["rerank_score"] = match_count / max(len(query_words), 1)
            
        sorted_docs = sorted(docs, key=lambda x: (x.metadata["rerank_score"], x.metadata.get("bm25_score", 0.0)), reverse=True)
        self._log_time(start_time)
        return sorted_docs[:top_n]

    def _log_time(self, start_time: float):
        elapsed = (time.time() - start_time) * 1000
        print(f"[Rerank] {self.provider} took {elapsed:.2f}ms")
