import re
from typing import List
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

class XanhSMBM25Retriever:
    """
    Highly optimized BM25 Keyword Retriever supporting Vietnamese and Role Pre-filtering.
    """
    
    def __init__(self):
        self.documents: List[Document] = []
        self.bm25: BM25Okapi = None
        
    def _tokenize(self, text: str) -> List[str]:
        # Simple lowercase word tokenization suited for Vietnamese keyword search
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s\d]', ' ', text)
        return text.split()

    def fit(self, documents: List[Document]):
        """
        Fits the BM25 model on a list of document chunks.
        """
        self.documents = documents
        
        if not self.documents:
            print("[WARN] Fitting BM25 on empty document list.")
            self.bm25 = None
            return
            
        tokenized_corpus = [self._tokenize(doc.page_content) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        print(f"[SUCCESS] Fitted BM25 index on {len(self.documents)} chunks.")

    def search(self, query: str, k: int = 15, role: str = None) -> List[Document]:
        """
        Performs BM25 keyword search with metadata pre-filtering by role.
        """
        if not self.bm25 or not self.documents:
            return []
            
        # 1. Filter documents based on role
        filtered_indices = []
        filtered_corpus_tokens = []
        
        target_role = role.lower() if role else None
        
        for idx, doc in enumerate(self.documents):
            doc_role = doc.metadata.get("role", "").lower()
            
            # If target_role is agent or none, matches everything. Otherwise role must match strictly.
            if not target_role or target_role == "agent" or doc_role == target_role:
                filtered_indices.append(idx)
                filtered_corpus_tokens.append(self._tokenize(doc.page_content))
                
        if not filtered_corpus_tokens:
            return []
            
        # 2. Run BM25 on filtered set
        temp_bm25 = BM25Okapi(filtered_corpus_tokens)
        tokenized_query = self._tokenize(query)
        
        # Calculate scores
        scores = temp_bm25.get_scores(tokenized_query)
        
        # Zip, sort and retrieve top k
        results_with_scores = []
        for i, score in enumerate(scores):
            original_idx = filtered_indices[i]
            doc = self.documents[original_idx]
            # Copy to avoid side effects
            matched_doc = Document(
                page_content=doc.page_content,
                metadata=doc.metadata.copy()
            )
            matched_doc.metadata["bm25_score"] = float(score)
            results_with_scores.append(matched_doc)
            
        # Sort descending
        sorted_results = sorted(results_with_scores, key=lambda x: x.metadata["bm25_score"], reverse=True)
        return sorted_results[:k]
