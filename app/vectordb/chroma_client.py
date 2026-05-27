import os
import traceback
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.ingestion.embedding import get_embeddings
from app.config import config

class XanhSMVectorDB:
    """
    ChromaDB layer for persistent dense semantic search.
    Supports Shared-State Singleton pattern for resilient Offline/Fallback executions.
    Avoids native C++ SQLite/Chroma crashes on Windows by checking config.CHROMA_PROVIDER.
    """
    
    # Class-level variables to share state across instantiations
    _vector_store = None
    _fallback_docs: List[Document] = []
    
    def __init__(self):
        self.embeddings = get_embeddings()
        self.persist_dir = config.CHROMA_PERSIST_DIR
        self.collection_name = config.CHROMA_COLLECTION_NAME
        
        # Enforce fallback provider immediately if configured to bypass native C++ DLL load entirely
        if config.CHROMA_PROVIDER == "fallback":
            if XanhSMVectorDB._vector_store is None:
                print("[INFO] Resilient In-Memory Fallback VectorDB enabled by config.")
                XanhSMVectorDB._vector_store = "fallback"
        else:
            if XanhSMVectorDB._vector_store is None:
                self._init_db()

    def _init_db(self):
        try:
            os.makedirs(self.persist_dir, exist_ok=True)
            XanhSMVectorDB._vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_dir
            )
            print(f"[OK] Persisted ChromaDB initialized at: {self.persist_dir}")
        except Exception as e:
            # Safe ASCII error log
            error_msg = f"[ERROR] Error initializing ChromaDB: {str(e)}"
            print(error_msg.encode('ascii', 'ignore').decode('ascii'))
            
            # Fallback to safe memory DB
            XanhSMVectorDB._vector_store = "fallback"
            print("[INFO] Fallback database active due to init error.")
            
            # Write traceback to error file
            try:
                with open("chroma_init_error.log", "w", encoding="utf-8") as f:
                    f.write(traceback.format_exc())
            except Exception:
                pass

    def add_documents(self, documents: List[Document]):
        if XanhSMVectorDB._vector_store is None or XanhSMVectorDB._vector_store == "fallback":
            XanhSMVectorDB._vector_store = "fallback"
            XanhSMVectorDB._fallback_docs.extend(documents)
            print(f"[SUCCESS] Added {len(documents)} chunks to Fallback DB. Total chunks: {len(XanhSMVectorDB._fallback_docs)}")
            return

        try:
            ids = [doc.metadata.get("chunk_id", f"doc_{i}") for i, doc in enumerate(documents)]
            XanhSMVectorDB._vector_store.add_documents(documents=documents, ids=ids)
            print(f"[SUCCESS] Added {len(documents)} chunks to ChromaDB.")
        except Exception as e:
            print(f"[WARN] Failed to write to ChromaDB: {str(e)}. Switching to In-Memory Fallback DB.")
            XanhSMVectorDB._vector_store = "fallback"
            XanhSMVectorDB._fallback_docs.extend(documents)
            print(f"[SUCCESS] Added {len(documents)} chunks to Fallback DB. Total chunks: {len(XanhSMVectorDB._fallback_docs)}")

    def search(self, query: str, k: int = 15, role: str = None) -> List[Document]:
        """
        Executes semantic search with metadata pre-filtering by role.
        """
        target_role = role.lower() if role else None
        
        if XanhSMVectorDB._vector_store == "fallback" or not isinstance(XanhSMVectorDB._vector_store, Chroma):
            # Direct text overlap search for fallback
            results = []
            for doc in XanhSMVectorDB._fallback_docs:
                doc_role = doc.metadata.get("role", "").lower()
                if not target_role or target_role == "agent" or doc_role == target_role or doc_role == "faq":
                    results.append(doc)
            return results[:k]

        # Role filtering logic: Allow matching the target role OR general shared FAQs
        search_filter = None
        if target_role and target_role != "agent":
            search_filter = {"role": {"$in": [target_role, "faq"]}}
            
        print(f"[INFO] Dense Vector Search for: '{query}' (Filter: {search_filter})")
        
        try:
            results = XanhSMVectorDB._vector_store.similarity_search(
                query=query,
                k=k,
                filter=search_filter
            )
            return results
        except Exception as e:
            print(f"[WARN] Dense search failed: {e}. Falling back to in-memory search.")
            results = []
            for doc in XanhSMVectorDB._fallback_docs:
                doc_role = doc.metadata.get("role", "").lower()
                if not target_role or target_role == "agent" or doc_role == target_role or doc_role == "faq":
                    results.append(doc)
            return results[:k]

    def clear(self):
        XanhSMVectorDB._fallback_docs = []
        if XanhSMVectorDB._vector_store and XanhSMVectorDB._vector_store != "fallback" and isinstance(XanhSMVectorDB._vector_store, Chroma):
            try:
                XanhSMVectorDB._vector_store.delete_collection()
                print("[SUCCESS] Cleared existing Chroma collection.")
                XanhSMVectorDB._vector_store = None
                self._init_db()
            except Exception as e:
                print(f"[ERROR] Error clearing collection: {e}")
        else:
            XanhSMVectorDB._vector_store = None
            print("[SUCCESS] Fallback DB Cleared.")
