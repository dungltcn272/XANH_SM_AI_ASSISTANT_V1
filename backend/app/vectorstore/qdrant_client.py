from __future__ import annotations

from urllib.parse import urlparse

from app.config.settings import settings


def _is_local_http(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "http" and host in {"localhost", "127.0.0.1", "0.0.0.0"}


def _api_key() -> str | None:
    if _is_local_http(settings.QDRANT_URL):
        return None
    return settings.QDRANT_API_KEY or None


def qdrant_settings() -> dict:
    return {"url": settings.QDRANT_URL, "has_api_key": bool(_api_key())}


def get_qdrant_client():
    try:
        from qdrant_client import QdrantClient
    except ModuleNotFoundError:
        return None
    return QdrantClient(url=settings.QDRANT_URL, api_key=_api_key(), timeout=30)
