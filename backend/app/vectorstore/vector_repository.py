from __future__ import annotations

import uuid
from typing import Any

from app.config.settings import settings
from app.integrations.openai_client import embed_texts
from app.vectorstore.collections import KNOWLEDGE_COLLECTION
from app.vectorstore.qdrant_client import get_qdrant_client


VECTOR_NAME = "dense"


def ensure_collection(collection: str = KNOWLEDGE_COLLECTION) -> bool:
    client = get_qdrant_client()
    if client is None:
        return False
    try:
        from qdrant_client.http import models

        names = {item.name for item in client.get_collections().collections}
        if collection in names:
            return True
        client.create_collection(
            collection_name=collection,
            vectors_config={VECTOR_NAME: models.VectorParams(size=settings.EMBEDDING_DIMENSIONS, distance=models.Distance.COSINE)},
        )
        return True
    except Exception:
        return False


def upsert_texts(items: list[dict[str, Any]], *, collection: str = KNOWLEDGE_COLLECTION) -> list[str]:
    client = get_qdrant_client()
    if client is None or not ensure_collection(collection):
        return []
    vectors = embed_texts([item["text"] for item in items])
    if not vectors or any(not vector for vector in vectors):
        return []
    try:
        from qdrant_client.http import models

        ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, item.get("id") or str(uuid.uuid4()))) for item in items]
        points = [
            models.PointStruct(
                id=ids[index],
                vector={VECTOR_NAME: vectors[index]},
                payload={"page_content": items[index]["text"], "metadata": items[index].get("metadata", {})},
            )
            for index in range(len(items))
        ]
        client.upsert(collection_name=collection, points=points)
        return ids
    except Exception:
        return []


def _query_points(client: Any, *, collection: str, vector: list[float], limit: int) -> list[Any]:
    if hasattr(client, "query_points"):
        try:
            return list(client.query_points(collection_name=collection, query=vector, using=VECTOR_NAME, limit=limit, with_payload=True).points)
        except Exception:
            try:
                return list(client.query_points(collection_name=collection, query=vector, limit=limit, with_payload=True).points)
            except Exception:
                return []
    if hasattr(client, "search"):
        try:
            return list(client.search(collection_name=collection, query_vector=(VECTOR_NAME, vector), limit=limit, with_payload=True))
        except Exception:
            try:
                return list(client.search(collection_name=collection, query_vector=vector, limit=limit, with_payload=True))
            except Exception:
                return []
    return []


def search_vectors(query: str, *, collection: str = KNOWLEDGE_COLLECTION, limit: int = 25) -> list[dict]:
    client = get_qdrant_client()
    if client is None:
        return []
    vector = embed_texts([query])[0]
    if not vector:
        return []
    results = _query_points(client, collection=collection, vector=vector, limit=limit)
    docs = []
    for item in results:
        payload = item.payload or {}
        metadata = payload.get("metadata", {})
        docs.append(
            {
                "content": payload.get("page_content", ""),
                "metadata": metadata,
                "score": float(item.score or 0),
                "retrieval_source": "qdrant_dense",
            }
        )
    return docs
