from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.assistant.memory.conversation_store import get_or_create_conversation, save_message
from app.assistant.orchestrator import XanhSMAssistantOrchestrator
from app.core.dependency import get_current_entity, get_db
from app.schemas.chat import ChatRequest


router = APIRouter()


def _actor_id(current_entity: dict) -> str | None:
    entity = current_entity.get("entity")
    return getattr(entity, "id", None)


def _stream_result(result: dict, *, conversation_id: str) -> Iterator[str]:
    yield f"data: {json.dumps({'conversation_id': conversation_id, 'run_id': result['run_id'], 'persona': result['persona']}, ensure_ascii=False)}\n\n"
    yield f"data: {json.dumps({'step': 'intent', 'intent': result['intent'], 'persona': result['persona']}, ensure_ascii=False)}\n\n"
    for event in result.get("metrics", {}).get("pipeline_trace", []):
        message = f"{event.get('node')}:{event.get('event')}"
        yield f"data: {json.dumps({'step': event.get('node'), 'event': event.get('event'), 'message': message, 'elapsed_ms': event.get('elapsed_ms')}, ensure_ascii=False)}\n\n"
    for line in result["answer"].splitlines():
        yield f"data: {line}\n\n"
    yield f"data: {json.dumps({'metrics': result['metrics'], 'tool_results': result['tool_results']}, ensure_ascii=False, default=str)}\n\n"
    yield "data: [DONE]\n\n"


@router.post("")
def chat_endpoint(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_entity: dict = Depends(get_current_entity),
) -> StreamingResponse:
    actor_id = _actor_id(current_entity)
    conversation = get_or_create_conversation(db, conversation_id=req.conversation_id, actor_id=actor_id, persona_id=req.persona)
    save_message(
        db,
        conversation_id=conversation.id,
        role="user",
        content=req.display_query or req.query,
        metadata={"persona": req.persona, "raw_query": req.query, "deep_search": req.deep_search, "has_image": bool(req.image_base64)},
    )

    orchestrator = XanhSMAssistantOrchestrator()
    result = orchestrator.run(
        query=req.query,
        persona=req.persona,
        actor_id=actor_id,
        conversation_id=conversation.id,
        db=db,
        lat=req.lat,
        lng=req.lng,
        address=req.address,
        budget_vnd=req.budget_vnd,
    )
    assistant_message = save_message(
        db,
        conversation_id=conversation.id,
        role="assistant",
        content=result["answer"],
        metadata={"run_id": result["run_id"], "persona": result["persona"], "metrics": result["metrics"], "tool_results": result["tool_results"]},
    )
    result["metrics"]["message_id"] = assistant_message.id

    return StreamingResponse(
        _stream_result(result, conversation_id=conversation.id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
