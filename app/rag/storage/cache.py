import json
from typing import List, Dict, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import SemanticCache
from app.ingestion.embedding import get_embedding_model
from app.core.logger import log_error

class XanhSMRAGCache:
    """
    Semantic Cache (PostgreSQL) using Exact Match and Cosine Similarity.
    Fallback to exact match only if vector logic fails.
    """
    def __init__(self):
        self.embeddings = get_embedding_model()

    def _is_probably_complete_answer(self, answer: str | None) -> bool:
        if not answer:
            return False
        clean = answer.strip()
        if not clean:
            return False
        lowered = clean.lower()
        if "hệ thống bị gián đoạn" in lowered or "câu trả lời có thể chưa hoàn chỉnh" in lowered:
            return False
        terminal_chars = {".", "!", "?", "…", ")", "]", "}", '"', "'", "ạ"}
        return clean[-1] in terminal_chars

    def get(self, query: str) -> Tuple[bool, Dict[str, Any], str]:
        q_clean = query.strip().lower()
        db: Session = SessionLocal()
        try:
            # 1. Exact Match
            exact_match = db.query(SemanticCache).filter(SemanticCache.query == q_clean).first()
            if exact_match:
                payload = json.loads(exact_match.response)
                answer = payload.get("answer")
                if not self._is_probably_complete_answer(answer):
                    db.delete(exact_match)
                    db.commit()
                    return False, {}, "invalid"
                return True, {
                    "answer": answer,
                    "citations": payload.get("citations", []),
                    "cache_hit": "exact"
                }, "exact"
                
            # 2. Semantic Match is currently disabled as we rely on exact matching for cache.
            # To prevent redundant network overhead (calling embed_query), we return False early.
            return False, {}, "none"
        except Exception as e:
            log_error("CACHE", f"Cache retrieval error: {e}")
            return False, {}, "none"
        finally:
            db.close()
            try:
                from app.db.database import engine
                engine.dispose()
            except Exception:
                pass
 
    def set(self, query: str, answer: str, citations: List[Dict[str, Any]]):
        q_clean = query.strip().lower()
        if not self._is_probably_complete_answer(answer):
            return
        db: Session = SessionLocal()
        try:
            # Check if exists
            existing = db.query(SemanticCache).filter(SemanticCache.query == q_clean).first()
            payload = json.dumps({"answer": answer, "citations": citations}, ensure_ascii=False)
            if existing:
                existing.response = payload
            else:
                new_cache = SemanticCache(query=q_clean, response=payload)
                db.add(new_cache)
            db.commit()
        except Exception as e:
            db.rollback()
            log_error("CACHE", f"Failed to save cache: {e}")
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
