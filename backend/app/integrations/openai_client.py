from __future__ import annotations

from collections.abc import Iterable, Iterator

from app.config.settings import settings


def openai_configured() -> bool:
    return bool(settings.OPENAI_API_KEY)


def _client():
    if not openai_configured():
        return None
    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.OPENAI_TIMEOUT_SECONDS)


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    items = [text or "" for text in texts]
    client = _client()
    if client is None or not items:
        return [[] for _ in items]
    response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=items,
        dimensions=settings.EMBEDDING_DIMENSIONS,
    )
    return [item.embedding for item in response.data]


def complete_text(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> str:
    client = _client()
    if client is None:
        return ""
    response = client.chat.completions.create(
        model=model or settings.RAG_ANSWER_MODEL,
        temperature=temperature,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def stream_text(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> Iterator[str]:
    client = _client()
    if client is None:
        return iter(())

    stream = client.chat.completions.create(
        model=model or settings.RAG_ANSWER_MODEL,
        temperature=temperature,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        stream=True,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    for event in stream:
        delta = event.choices[0].delta.content
        if delta:
            yield delta
