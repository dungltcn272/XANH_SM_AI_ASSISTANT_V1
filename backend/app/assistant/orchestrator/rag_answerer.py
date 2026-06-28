from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.assistant.prompts.rag_prompts import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT_TEMPLATE
from app.config.settings import settings
from app.domains.rag.services.context_service import KnowledgeContext, build_knowledge_context
from app.integrations.openai_client import complete_text, openai_configured, stream_text


def _fallback_answer(context: KnowledgeContext) -> str:
    if not context.chunks:
        return "Dạ, hiện em chưa có thông tin chi tiết phù hợp để trả lời chính xác. Anh/chị có thể hỏi rõ hơn hoặc liên hệ tổng đài 1900 2088 nếu cần hỗ trợ trực tiếp."
    preview = context.chunks[0].content.strip()[:900]
    return f"Dạ anh/chị, em tìm thấy nội dung liên quan như sau:\n\n{preview}"


def _answer_payload(answer: str, context: KnowledgeContext) -> dict:
    return {
        "answer": answer,
        "sources": context.sources,
        "retrieved_count": context.retrieved_count,
        "reranked_count": context.reranked_count,
    }


def answer_from_knowledge(query: str, *, db: Session | None = None, top_k: int | None = None) -> dict:
    if db is None:
        return {"answer": "RAG cần database session để truy xuất tài liệu.", "sources": []}
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
    return _answer_payload(answer, context)


def stream_answer_from_knowledge(query: str, *, db: Session | None = None, top_k: int | None = None) -> Iterator[dict]:
    if db is None:
        yield {"event": "error", "data": {"message": "RAG cần database session để truy xuất tài liệu."}}
        yield {"event": "done", "data": "[DONE]"}
        return

    context = build_knowledge_context(query, db=db, top_k=top_k)
    yield {
        "event": "sources",
        "data": {
            "sources": context.sources,
            "retrieved_count": context.retrieved_count,
            "reranked_count": context.reranked_count,
        },
    }

    if openai_configured() and context.text:
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
        yield {"event": "answer", "data": payload}
    else:
        answer = _fallback_answer(context)
        for line in answer.splitlines(keepends=True):
            yield {"event": "token", "data": line}
        yield {"event": "answer", "data": _answer_payload(answer, context)}

    yield {"event": "done", "data": "[DONE]"}
