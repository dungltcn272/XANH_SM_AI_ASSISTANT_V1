from typing import List
import unicodedata
from langchain_core.documents import Document
from app.config import config

class XanhSMReranker:
    """
    Reranker wrapper that re-scores documents using cross-attention.
    Supports HuggingFace bge-reranker-v2-m3 and premium light fallbacks.
    """
    
    def __init__(self):
        self.provider = config.RERANKER_PROVIDER.lower()
        self.model_name = config.RERANKER_MODEL
        self.model = None
        
        if self.provider == "local":
            try:
                from sentence_transformers import CrossEncoder
                self.model = CrossEncoder(self.model_name, max_length=512)
                print(f"[+] Initialized BGE Cross-Encoder reranker: {self.model_name}")
            except Exception as e:
                print(f"[!] SentenceTransformers CrossEncoder failed to load: {e}. Falling back to cosine relevance heuristic.")
                self.provider = "heuristic"
                
        if self.provider == "none" or self.provider == "":
            self.provider = "heuristic"

    def rerank(self, query: str, docs: List[Document], top_n: int = 5) -> List[Document]:
        if not docs:
            return []
            
        if self.provider == "local" and self.model:
            try:
                # Prepare query-document pairs
                pairs = [[query, doc.page_content] for doc in docs]
                scores = self.model.predict(pairs)
                
                # Assign scores
                for idx, score in enumerate(scores):
                    docs[idx].metadata["rerank_score"] = float(score)
                    
                sorted_docs = sorted(docs, key=lambda x: x.metadata["rerank_score"], reverse=True)
                return sorted_docs[:top_n]
            except Exception as e:
                print(f"[-] Error during local reranking: {e}. Falling back to heuristic.")
                
        # Heuristic Fallback: Calculates relevance score by exact word matches with accent stripping
        def clean_text(text: str) -> str:
            text = text.lower()
            normalized = unicodedata.normalize('NFKD', text)
            no_accents = ''.join([c for c in normalized if not unicodedata.combining(c)])
            no_accents = no_accents.replace('đ', 'd').replace('Đ', 'D')
            return no_accents

        clean_query = clean_text(query)
        query_words = set(clean_query.split())
        for doc in docs:
            clean_doc = clean_text(doc.page_content)
            doc_words = clean_doc.split()
            match_count = sum(1 for word in query_words if word in doc_words)
            # Normalize match score by query length
            score = match_count / max(len(query_words), 1)
            doc.metadata["rerank_score"] = score
            
        sorted_docs = sorted(sorted(docs, key=lambda x: x.metadata.get("bm25_score", 0.0), reverse=True), key=lambda x: x.metadata["rerank_score"], reverse=True)
        return sorted_docs[:top_n]

