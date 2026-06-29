from __future__ import annotations

import json
import math
import re
import unicodedata
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings as config
from app.core.logger import log_error, log_warn
from app.db.database import SessionLocal
from app.db.models import SemanticCache
from app.ingestion.embedding import get_embedding_model


class XanhSMRAGCache:
    """
    Hybrid semantic cache stored in PostgreSQL.

    Exact match is checked first. Semantic match uses a dense query embedding
    combined with a lightweight sparse token score over cached rewritten queries.
    New cache rows store embedding/tokens inside response JSON to avoid a schema
    migration while keeping the table replaceable later.
    """

    def __init__(self):
        self.embeddings = None
        if config.SEMANTIC_CACHE_ENABLED:
            try:
                from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
                self.embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
            except Exception as exc:
                log_warn("CACHE", f"Semantic cache embeddings disabled: {exc}")

    def _normalize_query(self, query: str) -> str:
        return " ".join((query or "").strip().lower().split())

    def _strip_accents(self, value: str) -> str:
        normalized = unicodedata.normalize("NFD", value or "")
        return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

    def _tokens(self, query: str) -> list[str]:
        clean = self._strip_accents(self._normalize_query(query))
        return re.findall(r"[a-z0-9]+", clean)

    def _sparse_score(self, query_tokens: list[str], cached_tokens: list[str]) -> float:
        if not query_tokens or not cached_tokens:
            return 0.0
        q_counts: dict[str, int] = {}
        c_counts: dict[str, int] = {}
        for token in query_tokens:
            q_counts[token] = q_counts.get(token, 0) + 1
        for token in cached_tokens:
            c_counts[token] = c_counts.get(token, 0) + 1
        common = set(q_counts) & set(c_counts)
        dot = sum(q_counts[token] * c_counts[token] for token in common)
        q_norm = math.sqrt(sum(value * value for value in q_counts.values()))
        c_norm = math.sqrt(sum(value * value for value in c_counts.values()))
        if not q_norm or not c_norm:
            return 0.0
        return dot / (q_norm * c_norm)

    def _dense_score(self, left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if not left_norm or not right_norm:
            return 0.0
        return dot / (left_norm * right_norm)

    def _embed_query(self, query: str) -> list[float] | None:
        if not self.embeddings:
            return None
        try:
            return list(self.embeddings.embed_query(query))
        except Exception as exc:
            log_warn("CACHE", f"Embedding query failed, falling back to exact cache only: {exc}")
            return None

    def _is_probably_complete_answer(self, answer: str | None) -> bool:
        if not answer:
            return False
        clean = answer.strip()
        if not clean:
            return False
        lowered = clean.lower()
        if "hệ thống bị gián đoạn" in lowered or "câu trả lời có thể chưa hoàn chỉnh" in lowered:
            return False
        if "há»‡ thá»‘ng bá»‹ giÃ¡n Ä‘oáº¡n" in lowered or "cÃ¢u tráº£ lá» i cÃ³ thá»ƒ chÆ°a hoÃ n chá»‰nh" in lowered:
            return False
        return True

    def _payload_from_row(self, row: SemanticCache) -> dict[str, Any] | None:
        try:
            payload = json.loads(row.response)
        except (TypeError, json.JSONDecodeError):
            return None
        if not self._is_probably_complete_answer(payload.get("answer")):
            return None
        return payload

    def get(self, query: str) -> Tuple[bool, Dict[str, Any], str]:
        q_clean = self._normalize_query(query)
        db: Session = SessionLocal()
        try:
            exact_match = db.query(SemanticCache).filter(SemanticCache.query == q_clean).first()
            if exact_match:
                payload = self._payload_from_row(exact_match)
                if not payload:
                    db.delete(exact_match)
                    db.commit()
                    return False, {}, "invalid"
                return True, self._hit_payload(payload, "exact", 1.0, 1.0, 1.0, exact_match.query), "exact"

            if not config.SEMANTIC_CACHE_ENABLED:
                return False, {}, "none"

            query_embedding = self._embed_query(q_clean)
            if not query_embedding:
                return False, {}, "none"

            query_tokens = self._tokens(q_clean)
            rows = (
                db.query(SemanticCache)
                .order_by(SemanticCache.created_at.desc())
                .limit(config.SEMANTIC_CACHE_MAX_ROWS)
                .all()
            )
            best: tuple[float, float, float, SemanticCache, dict[str, Any]] | None = None
            dense_weight = min(max(config.SEMANTIC_CACHE_DENSE_WEIGHT, 0.0), 1.0)
            sparse_weight = 1.0 - dense_weight

            for row in rows:
                payload = self._payload_from_row(row)
                if not payload:
                    continue
                cached_embedding = payload.get("query_embedding")
                if not isinstance(cached_embedding, list):
                    continue
                dense = self._dense_score(query_embedding, cached_embedding)
                sparse = self._sparse_score(query_tokens, payload.get("sparse_tokens") or self._tokens(row.query))
                hybrid = dense_weight * dense + sparse_weight * sparse
                if best is None or hybrid > best[0]:
                    best = (hybrid, dense, sparse, row, payload)

            if best and best[0] >= config.SEMANTIC_CACHE_HYBRID_THRESHOLD:
                hybrid, dense, sparse, row, payload = best
                return True, self._hit_payload(payload, "hybrid", hybrid, dense, sparse, row.query), "hybrid"
            return False, {}, "none"
        except Exception as exc:
            log_error("CACHE", f"Cache retrieval error: {exc}")
            return False, {}, "none"
        finally:
            db.close()

    def _hit_payload(
        self,
        payload: dict[str, Any],
        hit_type: str,
        hybrid_score: float,
        dense_score: float,
        sparse_score: float,
        matched_query: str,
    ) -> dict[str, Any]:
        return {
            "answer": payload.get("answer"),
            "citations": payload.get("citations", []),
            "cache_hit": hit_type,
            "cache_similarity": round(hybrid_score, 4),
            "cache_dense_similarity": round(dense_score, 4),
            "cache_sparse_similarity": round(sparse_score, 4),
            "cache_matched_query": matched_query,
        }

    def set(
        self,
        query: str,
        answer: str,
        citations: List[Dict[str, Any]],
        *,
        cache_policy: dict[str, Any] | None = None,
    ):
        q_clean = self._normalize_query(query)
        if not q_clean or not self._is_probably_complete_answer(answer):
            return
        policy = cache_policy or {"eligible": True, "reason": "legacy_caller"}
        if policy.get("eligible") is False:
            return

        query_embedding = self._embed_query(q_clean)
        payload = {
            "answer": answer,
            "citations": citations,
            "canonical_query": q_clean,
            "sparse_tokens": self._tokens(q_clean),
            "cache_policy": policy,
        }
        if query_embedding:
            payload["query_embedding"] = query_embedding

        db: Session = SessionLocal()
        try:
            existing = db.query(SemanticCache).filter(SemanticCache.query == q_clean).first()
            payload_json = json.dumps(payload, ensure_ascii=False)
            if existing:
                existing.response = payload_json
            else:
                db.add(SemanticCache(query=q_clean, response=payload_json))
            db.commit()
        except Exception as exc:
            db.rollback()
            log_error("CACHE", f"Failed to save cache: {exc}")
        finally:
            db.close()

    def clear(self):
        db: Session = SessionLocal()
        try:
            db.query(SemanticCache).delete()
            db.commit()
        finally:
            db.close()
