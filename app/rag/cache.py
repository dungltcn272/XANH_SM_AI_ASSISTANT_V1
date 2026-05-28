import os
import json
import sqlite3
import numpy as np
from typing import List, Dict, Any, Tuple
from app.config import config
from app.ingestion.embedding import get_embeddings

# Try to import psycopg2 for PostgreSQL support
try:
    import psycopg2
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

class XanhSMRAGCache:
    """
    Production-grade Dual-Driver (PostgreSQL / SQLite) cache system for Xanh SM RAG.
    Supports:
    1. Deterministic Cache (Exact String Match) -> Latency < 5ms.
    2. Semantic Cache (Embedding Cosine Similarity > 0.96) -> Latency < 20ms.
    Automatically uses PostgreSQL if DATABASE_URL env var is found (Railway default),
    otherwise falls back to lightweight local SQLite for seamless offline/local development.
    """
    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL")
        self.use_postgres = HAS_POSTGRES and self.db_url is not None
        self.embeddings = get_embeddings()
        
        if not self.use_postgres:
            self.db_path = os.path.join(config.CHROMA_PERSIST_DIR or "persistent_storage", "rag_cache.db")
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
        self._init_db()

    def _get_connection(self):
        if self.use_postgres:
            return psycopg2.connect(self.db_url)
        else:
            return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        if self.use_postgres:
            # PostgreSQL schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_cache (
                    id SERIAL PRIMARY KEY,
                    query TEXT NOT NULL,
                    query_vector TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    citations TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_query ON rag_cache (query)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_role ON rag_cache (role)")
        else:
            # SQLite schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    query_vector TEXT NOT NULL,  -- JSON list of float
                    answer TEXT NOT NULL,
                    citations TEXT NOT NULL,     -- JSON list of dicts
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_query ON rag_cache (query)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_role ON rag_cache (role)")
            
        conn.commit()
        conn.close()
        if self.use_postgres:
            print("[INFO] Production PostgreSQL Cache Database initialized.")
        else:
            print(f"[INFO] Local SQLite Cache Database initialized at: {self.db_path}")

    def get(self, query: str, role: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Retrieves cache for query and role.
        Returns (is_hit, result_dict, hit_type).
        """
        role = role.lower()
        q_clean = query.strip().lower()

        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. Exact Match
        if self.use_postgres:
            cursor.execute(
                "SELECT answer, citations FROM rag_cache WHERE LOWER(query) = %s AND role = %s LIMIT 1",
                (q_clean, role)
            )
        else:
            cursor.execute(
                "SELECT answer, citations FROM rag_cache WHERE LOWER(query) = ? AND role = ? LIMIT 1",
                (q_clean, role)
            )
            
        row = cursor.fetchone()
        if row:
            conn.close()
            answer, citations_json = row
            return True, {
                "answer": answer,
                "citations": json.loads(citations_json),
                "cache_hit": "exact"
            }, "exact"

        # 2. Semantic Match
        # Fetch all query records for this role
        if self.use_postgres:
            cursor.execute("SELECT query, query_vector, answer, citations FROM rag_cache WHERE role = %s", (role,))
        else:
            cursor.execute("SELECT query, query_vector, answer, citations FROM rag_cache WHERE role = ?", (role,))
            
        rows = cursor.fetchall()
        if not rows:
            conn.close()
            return False, {}, "none"

        # Get embedding vector of the current query
        query_vector = self.embeddings.embed_query(query)
        if all(v == 0.0 for v in query_vector):  # Mock embedding, skip semantic cache to avoid false positives
            conn.close()
            return False, {}, "none"

        # Calculate cosine similarity against all cached queries
        query_vector_np = np.array(query_vector)
        best_similarity = -1.0
        best_row = None

        for query_cached, vector_cached_json, answer, citations_json in rows:
            try:
                vector_cached = np.array(json.loads(vector_cached_json))
                # Cosine similarity
                dot_product = np.dot(query_vector_np, vector_cached)
                norm_q = np.linalg.norm(query_vector_np)
                norm_c = np.linalg.norm(vector_cached)
                if norm_q > 0 and norm_c > 0:
                    similarity = dot_product / (norm_q * norm_c)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_row = (answer, citations_json)
            except Exception:
                continue

        conn.close()

        # Semantic threshold: 0.96 (extremely high similarity to ensure accuracy)
        if best_similarity >= 0.96 and best_row:
            answer, citations_json = best_row
            return True, {
                "answer": answer,
                "citations": json.loads(citations_json),
                "cache_hit": "semantic",
                "cache_similarity": float(best_similarity)
            }, "semantic"

        return False, {}, "none"

    def set(self, query: str, answer: str, citations: List[Dict[str, Any]], role: str):
        """
        Stores response in cache.
        """
        role = role.lower()
        query_vector = self.embeddings.embed_query(query)
        
        # Don't cache mock zero vectors to prevent collision errors
        if all(v == 0.0 for v in query_vector):
            return

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if self.use_postgres:
                cursor.execute("DELETE FROM rag_cache WHERE query = %s AND role = %s", (query.strip(), role))
                cursor.execute(
                    "INSERT INTO rag_cache (query, query_vector, answer, citations, role) VALUES (%s, %s, %s, %s, %s)",
                    (query.strip(), json.dumps(query_vector), answer, json.dumps(citations), role)
                )
            else:
                cursor.execute(
                    "INSERT OR REPLACE INTO rag_cache (query, query_vector, answer, citations, role) VALUES (?, ?, ?, ?, ?)",
                    (query.strip(), json.dumps(query_vector), answer, json.dumps(citations), role)
                )
            conn.commit()
        except Exception as e:
            print(f"[WARN] Failed to write cache: {e}")
        finally:
            conn.close()

    def clear(self):
        """
        Clears cached entries. Called during database ingestion.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM rag_cache")
            conn.commit()
            print("[SUCCESS] Cleared RAG Cache Database.")
        except Exception as e:
            print(f"[WARN] Failed to clear cache: {e}")
        finally:
            conn.close()
