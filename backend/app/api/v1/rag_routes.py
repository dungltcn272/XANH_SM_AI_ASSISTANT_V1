from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.assistant.orchestrator.rag_answerer import answer_from_knowledge, stream_answer_from_knowledge
from app.core.dependency import get_db
from app.domains.rag.ingestion.ingestion_service import ingest_markdown, ingest_uri


router = APIRouter()


@router.get("/answer")
def answer(q: str, db: Session = Depends(get_db), top_k: int | None = None) -> dict:
    return answer_from_knowledge(q, db=db, top_k=top_k)


def _sse(events):
    for item in events:
        event = item.get("event", "message")
        data = item.get("data")
        if isinstance(data, str):
            payload = data
        else:
            payload = json.dumps(data, ensure_ascii=False, default=str)
        data_lines = payload.splitlines() or [""]
        yield f"event: {event}\n"
        for line in data_lines:
            yield f"data: {line}\n"
        yield "\n"


@router.get("/answer/stream")
def answer_stream(q: str, db: Session = Depends(get_db), top_k: int | None = None) -> StreamingResponse:
    return StreamingResponse(
        _sse(stream_answer_from_knowledge(q, db=db, top_k=top_k)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


class IngestRequest(BaseModel):
    uri: str | None = None
    title: str | None = None
    markdown: str | None = None
    category: str = "policy"
    access_scope: str = "public"
    document_type: str = "markdown"
    upsert_vectors: bool = True


@router.post("/ingest")
def ingest(req: IngestRequest, db: Session = Depends(get_db)) -> dict:
    if not req.uri and not req.markdown:
        raise HTTPException(status_code=400, detail="Cần truyền uri hoặc markdown.")
    if req.markdown:
        result = ingest_markdown(
            db,
            title=req.title or req.uri or "Manual document",
            markdown=req.markdown,
            uri=req.uri or f"manual://{abs(hash(req.markdown))}",
            category=req.category,
            access_scope=req.access_scope,
            document_type=req.document_type,
            upsert_vectors=req.upsert_vectors,
        )
    else:
        result = ingest_uri(
            db,
            req.uri or "",
            title=req.title,
            category=req.category,
            access_scope=req.access_scope,
            document_type=req.document_type,
            upsert_vectors=req.upsert_vectors,
        )
    return {"status": "ingested", **result}
