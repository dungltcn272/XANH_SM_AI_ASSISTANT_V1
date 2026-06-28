from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db.models import DocumentChunk
from app.vectorstore.collections import KNOWLEDGE_COLLECTION
from app.vectorstore.vector_repository import search_vectors


@dataclass
class RetrievedChunk:
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    retrieval_source: str = "unknown"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ỹ]+", (text or "").casefold())


def _metadata(row: DocumentChunk) -> dict:
    try:
        payload = json.loads(row.metadata_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    payload.setdefault("chunk_id", row.id)
    payload.setdefault("section", row.section_title)
    payload.setdefault("document_id", row.document_id)
    payload.setdefault("chunk_index", row.chunk_index)
    return payload


def _sql_bm25_search(db: Session, query: str, *, limit: int) -> list[RetrievedChunk]:
    rows = db.query(DocumentChunk).order_by(DocumentChunk.created_at.desc()).limit(2000).all()
    if not rows:
        return []
    corpus = [_tokenize(f"{row.section_title or ''} {row.content}") for row in rows]
    tokenized_query = _tokenize(query)
    if not tokenized_query:
        return []
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(tokenized_query)
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:limit]
    docs = []
    max_score = max([score for _, score in ranked] or [1.0]) or 1.0
    for index, score in ranked:
        if score <= 0:
            continue
        row = rows[index]
        docs.append(RetrievedChunk(content=row.content, metadata=_metadata(row), score=float(score / max_score), retrieval_source="sql_bm25"))
    return docs


def retrieve(query: str, *, db: Session, top_k: int | None = None) -> list[RetrievedChunk]:
    limit = top_k or settings.RETRIEVAL_CANDIDATE_LIMIT
    docs_by_id: dict[str, RetrievedChunk] = {}

    for item in search_vectors(query, collection=KNOWLEDGE_COLLECTION, limit=limit):
        metadata = item.get("metadata") or {}
        chunk_id = metadata.get("chunk_id") or item.get("content", "")[:80]
        docs_by_id[chunk_id] = RetrievedChunk(
            content=item.get("content", ""),
            metadata=metadata,
            score=float(item.get("score") or 0),
            retrieval_source=item.get("retrieval_source") or "qdrant_dense",
        )

    for doc in _sql_bm25_search(db, query, limit=limit):
        chunk_id = doc.metadata.get("chunk_id") or doc.content[:80]
        if chunk_id not in docs_by_id or doc.score > docs_by_id[chunk_id].score:
            docs_by_id[chunk_id] = doc

    docs = list(docs_by_id.values())
    docs.sort(key=lambda doc: doc.score, reverse=True)
    return docs[:limit]
