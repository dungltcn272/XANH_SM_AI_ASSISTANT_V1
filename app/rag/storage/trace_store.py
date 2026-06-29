from __future__ import annotations

import json
from typing import Any

from app.core.logger import log_warn
from app.db.models import RagRequestLog

def save_rag_request_log(
    *,
    conversation_id: str | None,
    user_id: str | None,
    guest_id: str | None,
    query: str,
    intent: str = "rag",
    metrics: dict[str, Any],
    retrieved_docs: list[Any] | None,
    reranked_docs: list[Any] | None,
    expanded_docs: list[Any] | None,
    final_answer: str | None = None,
) -> str | None:
    try:
        from app.db.database import SessionLocal

        db = SessionLocal()
        try:
            # Build JSON structures for docs
            retrieval_json = None
            if retrieved_docs:
                retrieval_json = json.dumps([{
                    "source": getattr(doc, "metadata", {}).get("source"),
                    "section": getattr(doc, "metadata", {}).get("section"),
                    "score": getattr(doc, "metadata", {}).get("score", 0),
                } for doc in retrieved_docs[:10]], ensure_ascii=False)
                
            rerank_json = None
            if reranked_docs:
                rerank_json = json.dumps([{
                    "source": getattr(doc, "metadata", {}).get("source"),
                    "section": getattr(doc, "metadata", {}).get("section"),
                    "rerank_score": getattr(doc, "metadata", {}).get("rerank_score", 0),
                } for doc in reranked_docs[:10]], ensure_ascii=False)
                
            parent_child_json = None
            if expanded_docs:
                parent_child_json = json.dumps([{
                    "source": getattr(doc, "metadata", {}).get("source"),
                    "section": getattr(doc, "metadata", {}).get("section"),
                } for doc in expanded_docs[:10]], ensure_ascii=False)

            log_entry = RagRequestLog(
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                original_query=query,
                rewritten_query=metrics.get("rewritten_query") or query,
                intent=intent,
                final_answer=final_answer,
                search_latency_ms=metrics.get("search_latency_ms", 0),
                generation_latency_ms=metrics.get("generation_latency_ms", 0),
                total_latency_ms=metrics.get("total_latency_ms", 0),
                rewrite_latency_ms=metrics.get("rewrite_latency_ms", 0),
                classification_latency_ms=metrics.get("classification_latency_ms", 0),
                expansion_latency_ms=metrics.get("expansion_latency_ms", 0),
                rerank_latency_ms=metrics.get("rerank_latency_ms", 0),
                cache_latency_ms=metrics.get("cache_latency_ms", 0),
                total_tokens=metrics.get("total_tokens", 0),
                cost_usd=metrics.get("cost_usd", 0.0),
                blocked_by_guardrail=metrics.get("blocked_by_guardrail", False),
                retrieval_result_json=retrieval_json,
                rerank_result_json=rerank_json,
                parent_child_result_json=parent_child_json,
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry.id
        finally:
            db.close()
    except Exception as exc:
        log_warn("RAG", f"Failed to save RAG request log: {exc}")
        return None
