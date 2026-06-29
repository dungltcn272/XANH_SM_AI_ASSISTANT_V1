from __future__ import annotations

import json
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.assistant.prompts.rag_prompts import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT_TEMPLATE
from app.cache.faq_cache import CuratedFaqCache
from app.cache.faq_candidate_analyzer import analyze_faq_candidate, is_cache_safe_query
from app.cache.faq_repository import SqlAlchemyFaqRepository
from app.config.settings import settings
from app.db.models import FaqCandidate
from app.domains.rag.rerankers.semantic_reranker import rerank_chunks
from app.domains.rag.retrievers.hybrid_retriever import retrieve
from app.domains.rag.services.context_service import KnowledgeContext, build_knowledge_context, _expand_context
from app.integrations.openai_client import complete_text, openai_configured, stream_text


def _fallback_answer(context: KnowledgeContext) -> str:
    if not context.chunks:
        return "Dạ, hiện em chưa có thông tin chi tiết phù hợp để trả lời chính xác. Anh/chị có thể hỏi rõ hơn hoặc liên hệ tổng đài 1900 2088 nếu cần hỗ trợ trực tiếp."
    preview = context.chunks[0].content.strip()[:900]
    return f"Dạ anh/chị, em tìm thấy nội dung liên quan như sau:\n\n{preview}"


def _text_chunks(text: str, *, target_size: int = 28) -> Iterator[str]:
    for index in range(0, len(text or ""), target_size):
        yield (text or "")[index : index + target_size]


def _answer_payload(answer: str, context: KnowledgeContext) -> dict:
    return {
        "answer": answer,
        "sources": context.sources,
        "retrieved_count": context.retrieved_count,
        "reranked_count": context.reranked_count,
    }


def _try_faq_cache(query: str, *, db: Session, persona_id: str, intent: str, run_id: str | None = None) -> dict | None:
    if not is_cache_safe_query(query, intent):
        return None
    result = CuratedFaqCache(SqlAlchemyFaqRepository(db)).get(query=query, persona_id=persona_id, intent=intent, run_id=run_id)
    if not result.hit:
        return None
    return {
        "answer": result.answer,
        "sources": [],
        "cache": {
            "type": "curated_faq",
            "hit": True,
            "faq_id": result.match.faq_id if result.match else None,
            "score": result.match.hybrid_score if result.match else None,
        },
        "retrieved_count": 0,
        "reranked_count": 0,
    }


def _save_faq_candidate(
    query: str,
    answer: str,
    *,
    db: Session,
    context: KnowledgeContext,
    persona_id: str,
    intent: str,
    run_id: str | None = None,
) -> None:
    source_ids = [str(source.get("document_id")) for source in context.sources if source.get("document_id")]
    analysis = analyze_faq_candidate(query, answer, intent, persona_id, source_ids=source_ids)
    if not analysis.eligible:
        return
    existing = (
        db.query(FaqCandidate)
        .filter(FaqCandidate.persona_id == persona_id, FaqCandidate.canonical_question == analysis.canonical_question, FaqCandidate.status == "candidate")
        .first()
    )
    if existing:
        existing.proposed_answer = answer
        existing.eligibility_score = analysis.score
        existing.reasons_json = json.dumps(list(analysis.reasons), ensure_ascii=False)
    else:
        db.add(
            FaqCandidate(
                run_id=run_id,
                persona_id=persona_id,
                user_query=query,
                canonical_question=analysis.canonical_question,
                proposed_answer=answer,
                eligibility_score=analysis.score,
                status="candidate",
                reasons_json=json.dumps(list(analysis.reasons), ensure_ascii=False),
            )
        )
    db.commit()


def answer_from_knowledge(
    query: str,
    *,
    db: Session | None = None,
    top_k: int | None = None,
    persona_id: str = "customer",
    intent: str = "rag",
    run_id: str | None = None,
) -> dict:
    if db is None:
        return {"answer": "RAG cần database session để truy xuất tài liệu.", "sources": []}
    cached = _try_faq_cache(query, db=db, persona_id=persona_id, intent=intent, run_id=run_id)
    if cached is not None:
        return cached
    context = build_knowledge_context(query, db=db, top_k=top_k)
    if openai_configured() and context.text:
        answer = complete_text(
            system_prompt=RAG_SYSTEM_PROMPT,
            user_prompt=RAG_USER_PROMPT_TEMPLATE.format(question=query, context=context.text, memory_context=""),
            model=settings.RAG_ANSWER_MODEL,
            temperature=0.2,
            max_tokens=2048,
        )
    else:
        answer = _fallback_answer(context)
    payload = _answer_payload(answer, context)
    _save_faq_candidate(query, payload["answer"], db=db, context=context, persona_id=persona_id, intent=intent, run_id=run_id)
    return payload


def stream_answer_from_knowledge(
    query: str,
    *,
    db: Session | None = None,
    top_k: int | None = None,
    persona_id: str = "customer",
    intent: str = "rag",
    run_id: str | None = None,
) -> Iterator[dict]:
    if db is None:
        yield {"event": "error", "data": {"message": "RAG cần database session để truy xuất tài liệu."}}
        yield {"event": "done", "data": "[DONE]"}
        return

    cached = _try_faq_cache(query, db=db, persona_id=persona_id, intent=intent, run_id=run_id)
    if cached is not None:
        yield {"event": "cache", "data": cached["cache"]}
        yield {"event": "progress", "data": {"step": "compose_start", "message": "Đang tổng hợp tài liệu"}}
        for token in _text_chunks(cached["answer"] or ""):
            yield {"event": "token", "data": token}
        yield {"event": "answer", "data": cached}
        yield {"event": "done", "data": "[DONE]"}
        return

    yield {"event": "progress", "data": {"step": "retrieval_start", "message": "Đang tìm kiếm tài liệu"}}
    candidates = retrieve(query, db=db, top_k=top_k or settings.RETRIEVAL_CANDIDATE_LIMIT)
    yield {"event": "progress", "data": {"step": "retrieval_done", "message": "Đã tìm thấy tài liệu liên quan", "retrieved_count": len(candidates)}}

    yield {"event": "progress", "data": {"step": "rerank_start", "message": "Đang xếp hạng tài liệu"}}
    reranked = rerank_chunks(query, candidates, top_n=settings.RERANK_TOP_N)
    yield {"event": "progress", "data": {"step": "rerank_done", "message": "Đã xếp hạng tài liệu", "reranked_count": len(reranked)}}

    yield {"event": "progress", "data": {"step": "expand_start", "message": "Đang mở rộng tài liệu lân cận"}}
    context_chunks = _expand_context(db, reranked)
    yield {"event": "progress", "data": {"step": "expand_done", "message": "Đã mở rộng tài liệu lân cận", "context_count": len(context_chunks)}}

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
    context = KnowledgeContext(query=query, chunks=context_chunks, sources=sources, retrieved_count=len(candidates), reranked_count=len(reranked))
    yield {
        "event": "sources",
        "data": {
            "sources": context.sources,
            "retrieved_count": context.retrieved_count,
            "reranked_count": context.reranked_count,
        },
    }

    if openai_configured() and context.text:
        yield {"event": "progress", "data": {"step": "compose_start", "message": "Đang tổng hợp tài liệu"}}
        answer_parts: list[str] = []
        for token in stream_text(
            system_prompt=RAG_SYSTEM_PROMPT,
            user_prompt=RAG_USER_PROMPT_TEMPLATE.format(question=query, context=context.text, memory_context=""),
            model=settings.RAG_ANSWER_MODEL,
            temperature=0.2,
            max_tokens=2048,
        ):
            answer_parts.append(token)
            yield {"event": "token", "data": token}
        payload = _answer_payload("".join(answer_parts), context)
        _save_faq_candidate(query, payload["answer"], db=db, context=context, persona_id=persona_id, intent=intent, run_id=run_id)
        yield {"event": "answer", "data": payload}
    else:
        yield {"event": "progress", "data": {"step": "compose_start", "message": "Đang tổng hợp tài liệu"}}
        answer = _fallback_answer(context)
        for token in _text_chunks(answer):
            yield {"event": "token", "data": token}
        payload = _answer_payload(answer, context)
        _save_faq_candidate(query, payload["answer"], db=db, context=context, persona_id=persona_id, intent=intent, run_id=run_id)
        yield {"event": "answer", "data": payload}

    yield {"event": "done", "data": "[DONE]"}
