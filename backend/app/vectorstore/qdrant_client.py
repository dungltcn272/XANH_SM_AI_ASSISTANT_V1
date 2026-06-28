from __future__ import annotations

from app.config.settings import settings


def qdrant_settings() -> dict:
    return {"url": settings.QDRANT_URL, "has_api_key": bool(settings.QDRANT_API_KEY)}


def get_qdrant_client():
    try:
        from qdrant_client import QdrantClient
    except ModuleNotFoundError:
        return None
    return QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None, timeout=30)
