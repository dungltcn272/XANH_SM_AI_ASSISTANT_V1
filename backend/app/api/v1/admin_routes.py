from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependency import get_current_admin, get_db
from app.db.models import AiTraceEvent, FaqCandidate, FaqEntry, FaqQuestionVariant
from app.schemas.response import HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service="xanhsm-backend", version="modular-v1")


@router.get("/me")
def admin_me(admin=Depends(get_current_admin)) -> dict:
    return {"id": admin.id, "email": admin.email, "role": admin.role.value}


@router.get("/trace-events")
def list_trace_events(
    conversation_id: str | None = None,
    run_id: str | None = None,
    node: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
) -> list[dict]:
    query = db.query(AiTraceEvent)
    if conversation_id:
        query = query.filter(AiTraceEvent.conversation_id == conversation_id)
    if node:
        query = query.filter(AiTraceEvent.node == node)
    rows = query.order_by(AiTraceEvent.created_at.desc()).limit(max(1, min(limit, 500))).all()
    result: list[dict] = []
    for row in rows:
        try:
            payload = json.loads(row.payload_json or "{}")
        except json.JSONDecodeError:
            payload = {"raw": row.payload_json}
        row_run_id = payload.get("run_id")
        if run_id and row_run_id != run_id:
            continue
        result.append(
            {
                "id": row.id,
                "run_id": row_run_id,
                "conversation_id": row.conversation_id,
                "persona_id": row.persona_id,
                "node": row.node,
                "event": row.event,
                "level": row.level,
                "payload": payload,
                "created_at": row.created_at,
            }
        )
    return result


class PublishFaqCandidateRequest(BaseModel):
    scope: str = "public"
    source_type: str = "assistant_candidate"
    status: str = "published"


@router.get("/faq-candidates")
def list_faq_candidates(
    status: str = "candidate",
    limit: int = 50,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
) -> list[dict]:
    rows = (
        db.query(FaqCandidate)
        .filter(FaqCandidate.status == status)
        .order_by(FaqCandidate.created_at.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return [
        {
            "id": row.id,
            "run_id": row.run_id,
            "persona_id": row.persona_id,
            "user_query": row.user_query,
            "canonical_question": row.canonical_question,
            "proposed_answer": row.proposed_answer,
            "eligibility_score": row.eligibility_score,
            "status": row.status,
            "reasons_json": row.reasons_json,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.post("/faq-candidates/{candidate_id}/publish")
def publish_faq_candidate(
    candidate_id: str,
    req: PublishFaqCandidateRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
) -> dict:
    candidate = db.query(FaqCandidate).filter(FaqCandidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="FAQ candidate not found")
    if not candidate.proposed_answer:
        raise HTTPException(status_code=400, detail="FAQ candidate has no answer")

    entry = FaqEntry(
        persona_id=candidate.persona_id or "customer",
        canonical_question=candidate.canonical_question,
        canonical_answer=candidate.proposed_answer,
        intent="rag",
        scope=req.scope,
        status=req.status,
        source_type=req.source_type,
        source_id=candidate.id,
    )
    db.add(entry)
    db.flush()
    db.add(
        FaqQuestionVariant(
            faq_entry_id=entry.id,
            question_text=candidate.user_query,
            normalized_question=" ".join(candidate.user_query.lower().split()),
        )
    )
    candidate.status = "published"
    db.commit()
    db.refresh(entry)
    return {"status": "published", "faq_entry_id": entry.id, "candidate_id": candidate.id}


@router.post("/faq-candidates/{candidate_id}/reject")
def reject_faq_candidate(candidate_id: str, db: Session = Depends(get_db), admin=Depends(get_current_admin)) -> dict:
    candidate = db.query(FaqCandidate).filter(FaqCandidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="FAQ candidate not found")
    candidate.status = "rejected"
    db.commit()
    return {"status": "rejected", "candidate_id": candidate.id}
