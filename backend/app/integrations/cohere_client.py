from __future__ import annotations

from functools import lru_cache

from app.config.settings import settings


def cohere_configured() -> bool:
    return bool(settings.COHERE_API_KEY)


@lru_cache(maxsize=4)
def _cohere_client(api_key: str):
    import cohere

    return cohere.Client(api_key)


def rerank(query: str, documents: list[str], *, top_n: int | None = None) -> list[dict]:
    if not cohere_configured() or not documents:
        return [
            {"index": index, "relevance_score": max(0.0, 1.0 - index * 0.05)}
            for index, _ in enumerate(documents[: top_n or len(documents)])
        ]
    try:
        import cohere
    except ModuleNotFoundError:
        return [
            {"index": index, "relevance_score": max(0.0, 1.0 - index * 0.05)}
            for index, _ in enumerate(documents[: top_n or len(documents)])
        ]
    client = _cohere_client(settings.COHERE_API_KEY)
    response = client.rerank(
        model=settings.RERANKER_MODEL,
        query=query,
        documents=documents,
        top_n=top_n or settings.RERANK_TOP_N,
    )
    return [{"index": item.index, "relevance_score": float(item.relevance_score)} for item in response.results]
