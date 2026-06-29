from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db.models import DocumentChunk
from app.vectorstore.collections import KNOWLEDGE_COLLECTION
from app.vectorstore.vector_repository import search_vectors


_DENSE_SEARCH_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="rag_dense")
RRF_K = 60


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


def _dense_chunks(items: list[dict]) -> list[RetrievedChunk]:
    chunks = []
    for item in items:
        metadata = item.get("metadata") or {}
        chunks.append(
            RetrievedChunk(
                content=item.get("content", ""),
                metadata=metadata,
                score=float(item.get("score") or 0),
                retrieval_source=item.get("retrieval_source") or "qdrant_dense",
            )
        )
    return chunks


def _chunk_key(chunk: RetrievedChunk) -> str:
    return str(chunk.metadata.get("chunk_id") or chunk.content[:80])


def _rrf_fuse(*ranked_lists: list[RetrievedChunk], limit: int, rrf_k: int = RRF_K) -> list[RetrievedChunk]:
    fused: dict[str, RetrievedChunk] = {}
    scores: dict[str, float] = {}
    sources: dict[str, list[str]] = {}

    for ranked in ranked_lists:
        for rank, chunk in enumerate(ranked, start=1):
            key = _chunk_key(chunk)
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
            sources.setdefault(key, [])
            if chunk.retrieval_source not in sources[key]:
                sources[key].append(chunk.retrieval_source)
            if key not in fused or chunk.score > fused[key].score:
                fused[key] = chunk

    output = []
    for key, chunk in fused.items():
        chunk.score = scores[key]
        chunk.metadata["rrf_score"] = scores[key]
        chunk.metadata["retrieval_sources"] = sources[key]
        chunk.retrieval_source = "+".join(sources[key])
        output.append(chunk)

    output.sort(key=lambda chunk: chunk.score, reverse=True)
    return output[:limit]


def retrieve(query: str, *, db: Session, top_k: int | None = None) -> list[RetrievedChunk]:
    limit = top_k or settings.RETRIEVAL_CANDIDATE_LIMIT

    dense_future = _DENSE_SEARCH_EXECUTOR.submit(search_vectors, query, collection=KNOWLEDGE_COLLECTION, limit=limit)
    sparse_docs = _sql_bm25_search(db, query, limit=limit)

    try:
        dense_items = dense_future.result()
    except Exception:
        dense_items = []

    dense_docs = _dense_chunks(dense_items)
    return _rrf_fuse(dense_docs, sparse_docs, limit=limit)
