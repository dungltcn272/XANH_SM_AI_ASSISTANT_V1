from __future__ import annotations

from app.config.settings import settings
from app.domains.rag.retrievers.hybrid_retriever import RetrievedChunk
from app.integrations.cohere_client import rerank


def rerank_chunks(query: str, candidates: list[RetrievedChunk], *, top_n: int | None = None) -> list[RetrievedChunk]:
    top_n = top_n or settings.RERANK_TOP_N
    if not candidates:
        return []
    results = rerank(query, [candidate.content for candidate in candidates], top_n=min(top_n, len(candidates)))
    output = []
    for item in results:
        candidate = candidates[item["index"]]
        candidate.metadata["rerank_score"] = item["relevance_score"]
        candidate.score = item["relevance_score"]
        output.append(candidate)
    output.sort(key=lambda doc: doc.score, reverse=True)
    return output[:top_n]
