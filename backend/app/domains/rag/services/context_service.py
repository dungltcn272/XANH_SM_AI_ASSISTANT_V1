from __future__ import annotations

import json
from dataclasses import dataclass

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


def _expand_context(db: Session, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    expanded: list[RetrievedChunk] = []
    seen: set[str] = set()
    for chunk in chunks:
        metadata = chunk.metadata or {}
        chunk_id = metadata.get("chunk_id")
        chunk_type = metadata.get("chunk_type")
        derived_from = metadata.get("derived_from")
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
        if parent_id and rerank_score >= settings.CONTEXT_EXPANSION_THRESHOLD:
            rows = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.metadata_json.contains(parent_id))
                .order_by(DocumentChunk.chunk_index.asc())
                .limit(settings.MAX_CHUNKS_PER_SECTION)
                .all()
            )
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
    candidates = retrieve(query, db=db, top_k=top_k or settings.RETRIEVAL_CANDIDATE_LIMIT)
    reranked = rerank_chunks(query, candidates, top_n=settings.RERANK_TOP_N)
    context_chunks = _expand_context(db, reranked)
    sources = [
        {
            "chunk_id": chunk.metadata.get("chunk_id"),
            "section": chunk.metadata.get("section"),
            "document_id": chunk.metadata.get("document_id"),
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
