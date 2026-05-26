from typing import List, Dict, Any
from langchain_core.documents import Document
from app.vectordb.chroma_client import XanhSMVectorDB
from app.retrieval.bm25_retriever import XanhSMBM25Retriever
from app.retrieval.multi_query import XanhSMQueryExpansion
from app.ingestion.splitter import HeadingAwareSplitter
from app.config import config

class XanhSMHybridSearch:
    """
    State-of-the-art Hybrid Search pipeline:
    Query Expansion ➔ Dense Search (Chroma) + Sparse Search (BM25) ➔ Reciprocal Rank Fusion (RRF).
    """
    
    def __init__(self):
        self.db = XanhSMVectorDB()
        self.bm25_retriever = XanhSMBM25Retriever()
        self.expander = XanhSMQueryExpansion()
        self.splitter = HeadingAwareSplitter()
        
        # Fit BM25 corpus on initialization
        self._fit_bm25_corpus()

    def _fit_bm25_corpus(self):
        """
        Loads and splits all local documents to build the BM25 index.
        Also populates the in-memory fallback VectorDB if enabled.
        """
        print("[INFO] Loading files to build BM25 sparse index...")
        try:
            chunks = self.splitter.split_directory(config.DATA_DIR)
            self.bm25_retriever.fit(chunks)
            
            # Resilient auto-load for Fallback Vector DB on startup
            if config.CHROMA_PROVIDER == "fallback":
                self.db.clear()
                self.db.add_documents(chunks)
        except Exception as e:
            print(f"[ERROR] Failed to build BM25 corpus: {e}")

    def reciprocal_rank_fusion(self, dense_runs: List[List[Document]], sparse_runs: List[List[Document]], k: int = 60) -> List[Document]:
        """
        Reciprocal Rank Fusion (RRF) algorithm.
        Merges multi-run dense and sparse retrieval ranks into a single scoring system.
        """
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}
        
        # Helper function to process individual runs
        def process_run(run_results: List[Document]):
            for rank, doc in enumerate(run_results):
                doc_id = doc.metadata.get("chunk_id") or doc.metadata.get("id") or doc.page_content[:100]
                doc_map[doc_id] = doc
                
                score = 1.0 / (k + rank + 1)
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + score

        for run in dense_runs:
            process_run(run)
        for run in sparse_runs:
            process_run(run)
            
        if not rrf_scores:
            return []
            
        sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        merged_docs = []
        for doc_id, score in sorted_ids:
            doc = doc_map[doc_id]
            copied_doc = Document(
                page_content=doc.page_content,
                metadata=doc.metadata.copy()
            )
            copied_doc.metadata["rrf_score"] = score
            merged_docs.append(copied_doc)
            
        return merged_docs

    def search(self, query: str, role: str = None, limit: int = 25) -> List[Document]:
        """
        Runs Multi-Query Expansion, Hybrid Retrieval, and fuses scores.
        """
        expanded_queries = self.expander.get_queries(query)
        print(f"[INFO] Expanded queries for search: {expanded_queries}")
        
        dense_runs: List[List[Document]] = []
        sparse_runs: List[List[Document]] = []
        
        for q in expanded_queries:
            dense_res = self.db.search(query=q, k=limit, role=role)
            dense_runs.append(dense_res)
            
            sparse_res = self.bm25_retriever.search(query=q, k=limit, role=role)
            sparse_runs.append(sparse_res)
            
        fused_docs = self.reciprocal_rank_fusion(dense_runs, sparse_runs)
        
        print(f"[SUCCESS] Hybrid Search matched {len(fused_docs)} unified documents.")
        return fused_docs[:limit]
