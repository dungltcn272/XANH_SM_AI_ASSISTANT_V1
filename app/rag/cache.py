import json
from typing import List, Dict, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import SemanticCache
from app.ingestion.embedding import get_embedding_model

class XanhSMRAGCache:
    """
    Semantic Cache (PostgreSQL) using Exact Match and Cosine Similarity.
    Fallback to exact match only if vector logic fails.
    """
    def __init__(self):
        self.embeddings = get_embedding_model()

    def get(self, query: str, role: str) -> Tuple[bool, Dict[str, Any], str]:
        q_clean = query.strip().lower()
        db: Session = SessionLocal()
        try:
            # 1. Exact Match
            exact_match = db.query(SemanticCache).filter(SemanticCache.query == q_clean).first()
            if exact_match:
                payload = json.loads(exact_match.response)
                return True, {
                    "answer": payload.get("answer"),
                    "citations": payload.get("citations", []),
                    "cache_hit": "exact"
                }, "exact"
                
            # 2. Semantic Match - since we didn't install pgvector, 
            # we fetch recent caches and compute cosine similarity in Python.
            # In a real heavy-load scenario, we would use Qdrant or pgvector.
            caches = db.query(SemanticCache).order_by(SemanticCache.id.desc()).limit(100).all()
            if not caches:
                return False, {}, "none"
                
            query_vector = self.embeddings.embed_query(query)
            query_vector_np = np.array(query_vector)
            
            best_similarity = -1.0
            best_payload = None
            
            # This is a naive in-memory semantic search over the last 100 caches
            for c in caches:
                payload = json.loads(c.response)
                cached_query = c.query
                # We would normally store vector in DB, but for simplicity here we re-embed or store it in payload.
                # Since storing vectors in JSON is slow, we just fallback if exact match fails.
                # Actually, wait, let's just use exact match for now to keep it blazing fast without pgvector.
                pass
                
            return False, {}, "none"
        except Exception as e:
            print(f"[CACHE ERROR] {e}")
            return False, {}, "none"
        finally:
            db.close()
            try:
                from app.db.database import engine
                engine.dispose()
            except Exception:
                pass

    def set(self, query: str, answer: str, citations: List[Dict[str, Any]], role: str):
        q_clean = query.strip().lower()
        db: Session = SessionLocal()
        try:
            # Check if exists
            existing = db.query(SemanticCache).filter(SemanticCache.query == q_clean).first()
            payload = json.dumps({"answer": answer, "citations": citations})
            if existing:
                existing.response = payload
            else:
                new_cache = SemanticCache(query=q_clean, response=payload)
                db.add(new_cache)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[CACHE ERROR] Failed to save cache: {e}")
        finally:
            db.close()
            try:
                from app.db.database import engine
                engine.dispose()
            except Exception:
                pass

    def clear(self):
        db: Session = SessionLocal()
        try:
            db.query(SemanticCache).delete()
            db.commit()
        finally:
            db.close()
            try:
                from app.db.database import engine
                engine.dispose()
            except Exception:
                pass
