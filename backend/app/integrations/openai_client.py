from __future__ import annotations

from collections.abc import Iterable, Iterator
import logging

from app.config.settings import settings


logger = logging.getLogger(__name__)
_openai_disabled_reason: str | None = None


def openai_configured() -> bool:
    return bool(settings.OPENAI_API_KEY) and _openai_disabled_reason is None


def _chat_model(*, model: str | None = None, temperature: float = 0.2, max_tokens: int | None = None):
    if not openai_configured():
        return None
    try:
        from langchain_openai import ChatOpenAI
    except ModuleNotFoundError:
        return None
    return ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model=model or settings.RAG_ANSWER_MODEL,
        temperature=temperature,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        timeout=settings.OPENAI_TIMEOUT_SECONDS,
    )


def _embedding_model():
    if not openai_configured():
        return None
    try:
        from langchain_openai import OpenAIEmbeddings
    except ModuleNotFoundError:
        return None
    return OpenAIEmbeddings(
        api_key=settings.OPENAI_API_KEY,
        model=settings.EMBEDDING_MODEL,
        dimensions=settings.EMBEDDING_DIMENSIONS,
        timeout=settings.OPENAI_TIMEOUT_SECONDS,
    )


def _handle_openai_error(exc: Exception) -> None:
    global _openai_disabled_reason
    status_code = getattr(exc, "status_code", None)
    message = str(exc)
    if status_code == 401 or "401" in message or "invalid_api_key" in message.lower():
        _openai_disabled_reason = "unauthorized"
        logger.warning("OpenAI disabled for this process because API authentication failed. Check OPENAI_API_KEY.")
        return
    logger.warning("OpenAI request failed: %s", exc)


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    items = [text or "" for text in texts]
    embeddings = _embedding_model()
    if embeddings is None or not items:
        return [[] for _ in items]
    try:
        return embeddings.embed_documents(items)
    except Exception as exc:
        _handle_openai_error(exc)
        return [[] for _ in items]


def complete_text(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> str:
    chat = _chat_model(model=model, temperature=temperature, max_tokens=max_tokens)
    if chat is None:
        return ""
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        response = chat.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        return str(response.content or "")
    except Exception as exc:
        _handle_openai_error(exc)
        return ""


def stream_text(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> Iterator[str]:
    chat = _chat_model(model=model, temperature=temperature, max_tokens=max_tokens)
    if chat is None:
        return iter(())

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        for event in chat.stream([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]):
            if event.content:
                yield str(event.content)
    except Exception as exc:
        _handle_openai_error(exc)
        return
