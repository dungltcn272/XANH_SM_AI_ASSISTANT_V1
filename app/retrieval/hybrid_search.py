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
        Also populates the in-memory fallback VectorDB if enabled or auto-populates ChromaDB if active but empty.
        """
        # --- Resilient Auto-Sync for Persistent Railway Volume ---
        import shutil
        import os
        
        default_data_dir = "./data"
        target_data_dir = config.DATA_DIR
        
        abs_default = os.path.abspath(default_data_dir)
        abs_target = os.path.abspath(target_data_dir)
        
        if abs_default != abs_target:
            has_files = False
            if os.path.exists(abs_target):
                for root, dirs, files in os.walk(abs_target):
                    if files:
                        has_files = True
                        break
            
            if not has_files and os.path.exists(abs_default):
                print(f"[INFO] Target DATA_DIR '{target_data_dir}' is empty. Copying default bundled files from '{default_data_dir}'...")
                try:
                    os.makedirs(abs_target, exist_ok=True)
                    for item in os.listdir(abs_default):
                        s = os.path.join(abs_default, item)
                        d = os.path.join(abs_target, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                    print("[OK] Bundled files copied to persistent volume successfully!")
                except Exception as e:
                    print(f"[WARN] Failed to copy default files: {e}")
        # ---------------------------------------------------------

        print("[INFO] Loading files to build BM25 sparse index...")
        try:
            chunks = self.splitter.split_directory(config.DATA_DIR)
            self.bm25_retriever.fit(chunks)
            
            # Resilient auto-load for Fallback Vector DB on startup
            if config.CHROMA_PROVIDER == "fallback":
                self.db.clear()
                self.db.add_documents(chunks)
            elif config.CHROMA_PROVIDER == "chromadb" and chunks:
                from langchain_community.vectorstores import Chroma
                if self.db._vector_store and isinstance(self.db._vector_store, Chroma):
                    try:
                        count = self.db._vector_store._collection.count()
                        if count == 0:
                            print("[INFO] Chroma DB is empty on startup. Automatically populating from preloaded data...")
                            self.db.add_documents(chunks)
                            print("[OK] Smart auto-ingestion completed on startup!")
                    except Exception as ex:
                        print(f"[WARN] Failed to auto-populate Chroma DB: {ex}")
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

    def search(self, query: str, role: str = None, limit: int = 25, expanded_queries: List[str] = None) -> List[Document]:
        """
        Runs Multi-Query Expansion, Hybrid Retrieval, and fuses scores.
        """
        if expanded_queries is None:
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
