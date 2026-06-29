from __future__ import annotations

import json
from dataclasses import dataclass
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db.models import DocumentChunk
from app.domains.rag.rerankers.semantic_reranker import rerank_chunks
from app.domains.rag.retrievers.hybrid_retriever import RetrievedChunk, retrieve


@dataclass
class KnowledgeContext:
    query: str
    chunks: list[RetrievedChunk]
    sources: list[dict]
    retrieved_count: int
    reranked_count: int

    @property
    def text(self) -> str:
        return "\n\n---\n\n".join(f"[{idx + 1}] {chunk.content}" for idx, chunk in enumerate(self.chunks))


def _as_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _expand_context(db: Session, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    expanded: list[RetrievedChunk] = []
    seen: set[str] = set()
    max_section_chunks = max(1, settings.MAX_CHUNKS_PER_SECTION)
    for rank, chunk in enumerate(chunks, start=1):
        metadata = chunk.metadata or {}
        chunk_id = metadata.get("chunk_id")
        chunk_type = metadata.get("chunk_type")
        derived_from = metadata.get("derived_from")
        document_id = metadata.get("document_id")
        chunk_index = _as_int(metadata.get("chunk_index"))
        rerank_score = float(metadata.get("rerank_score") or chunk.score or 0)

        if chunk_type == "table_row_index" and derived_from:
            row = db.query(DocumentChunk).filter_by(id=derived_from).first()
            if row and row.id not in seen:
                try:
                    row_meta = json.loads(row.metadata_json or "{}")
                except json.JSONDecodeError:
                    row_meta = {}
                row_meta["retrieval_source"] = "table_full_expansion"
                row_meta["expanded_from"] = chunk_id
                expanded.append(RetrievedChunk(content=row.content, metadata=row_meta, score=rerank_score, retrieval_source="table_full_expansion"))
                seen.add(row.id)
                continue

        parent_id = metadata.get("parent_chunk_id")
        if parent_id and chunk_type != "html_table_full" and rank <= settings.RERANK_TOP_N:
            query = db.query(DocumentChunk).filter(DocumentChunk.metadata_json.contains(parent_id))
            if document_id:
                query = query.filter(DocumentChunk.document_id == document_id)
            if chunk_index is not None:
                half_window = max_section_chunks // 2
                query = query.filter(
                    DocumentChunk.chunk_index >= max(0, chunk_index - half_window),
                    DocumentChunk.chunk_index <= chunk_index + half_window,
                )
            rows = query.order_by(DocumentChunk.chunk_index.asc()).limit(max_section_chunks).all()
            if rows:
                content = "\n\n".join(row.content for row in rows)
                if parent_id not in seen:
                    expanded.append(
                        RetrievedChunk(
                            content=content,
                            metadata={**metadata, "retrieval_source": "parent_section_expansion"},
                            score=rerank_score,
                            retrieval_source="parent_section_expansion",
                        )
                    )
                    seen.add(parent_id)
                continue

        if chunk_id not in seen:
            expanded.append(chunk)
            if chunk_id:
                seen.add(chunk_id)
    return expanded


def build_knowledge_context(query: str, *, db: Session, top_k: int | None = None) -> KnowledgeContext:
    return build_knowledge_context_with_progress(query, db=db, top_k=top_k)


def build_knowledge_context_with_progress(
    query: str,
    *,
    db: Session,
    top_k: int | None = None,
    on_step: Callable[[str, dict], None] | None = None,
) -> KnowledgeContext:
    def emit(step: str, **payload: object) -> None:
        if on_step is not None:
            on_step(step, payload)

    emit("retrieval_start", message="Đang tìm kiếm tài liệu")
    candidates = retrieve(query, db=db, top_k=top_k or settings.RETRIEVAL_CANDIDATE_LIMIT)
    emit("retrieval_done", message="Đã tìm thấy tài liệu liên quan", retrieved_count=len(candidates))

    emit("rerank_start", message="Đang xếp hạng tài liệu")
    reranked = rerank_chunks(query, candidates, top_n=settings.RERANK_TOP_N)
    emit("rerank_done", message="Đã xếp hạng tài liệu", reranked_count=len(reranked))

    emit("expand_start", message="Đang mở rộng tài liệu lân cận")
    context_chunks = _expand_context(db, reranked)
    emit("expand_done", message="Đã mở rộng tài liệu lân cận", context_count=len(context_chunks))

    sources = [
        {
            "chunk_id": chunk.metadata.get("chunk_id"),
            "section": chunk.metadata.get("section"),
            "document_id": chunk.metadata.get("document_id"),
            "source": chunk.metadata.get("source") or chunk.metadata.get("title") or chunk.metadata.get("document_id"),
            "title": chunk.metadata.get("title") or chunk.metadata.get("section"),
            "url": chunk.metadata.get("url"),
            "category": chunk.metadata.get("category"),
            "score": chunk.score,
            "retrieval_source": chunk.retrieval_source,
        }
        for chunk in context_chunks
    ]
    return KnowledgeContext(
        query=query,
        chunks=context_chunks,
        sources=sources,
        retrieved_count=len(candidates),
        reranked_count=len(reranked),
    )
