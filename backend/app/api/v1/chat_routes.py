from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.assistant.memory.context_builder import build_assistant_context
from app.assistant.memory.conversation_store import get_or_create_conversation, save_message
from app.assistant.nlu import analyze_intent
from app.assistant.orchestrator.rag_answerer import stream_answer_from_knowledge
from app.assistant.orchestrator.response_composer import compose_response
from app.assistant.orchestrator.task_planner import plan_tools
from app.assistant.orchestrator.tool_executor import ToolExecutionError, ToolPermissionError, execute_tool
from app.assistant.policies.safety_guard import is_safe_query
from app.core.logging.pipeline_trace import PipelineTracer
from app.core.dependency import get_current_entity, get_db
from app.schemas.chat import ChatRequest


router = APIRouter()


def _actor_id(current_entity: dict) -> str | None:
    entity = current_entity.get("entity")
    return getattr(entity, "id", None)


def _sse(payload: dict | str) -> str:
    if payload == "[DONE]":
        return "data: [DONE]\n\n"
    return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"


def _text_chunks(text: str, *, target_size: int = 28) -> Iterator[str]:
    for index in range(0, len(text or ""), target_size):
        yield (text or "")[index : index + target_size]


def _progress(message: str, *, step: str, tracer: PipelineTracer | None = None, **payload: object) -> str:
    if tracer is not None:
        tracer.emit(step, "progress", message=message, **payload)
    return _sse({"type": "progress", "step": step, "message": message, **payload})


def _top_sources(output: dict) -> list[dict]:
    sources = output.get("sources")
    if not isinstance(sources, list):
        return []
    return [
        {
            "chunk_id": source.get("chunk_id"),
            "section": source.get("section"),
            "score": source.get("score"),
            "retrieval_source": source.get("retrieval_source"),
        }
        for source in sources[:3]
        if isinstance(source, dict)
    ]


def _stream_chat(
    *,
    req: ChatRequest,
    db: Session,
    actor_id: str | None,
    conversation_id: str,
) -> Iterator[str]:
    started = time.perf_counter()
    run_id = f"run_{uuid.uuid4().hex}"
    persona = req.persona
    query = req.query
    tracer = PipelineTracer(run_id=run_id, conversation_id=conversation_id, persona_id=persona, db=db)
    tracer.start_run(actor_id=actor_id)
    tracer.emit("api", "run_start", query=query, actor_id=actor_id)

    answer_parts: list[str] = []
    tool_results: list[dict] = []
    first_token_latency_ms: float | None = None
    stream_sources = None
    intent = "rag"
    rewritten_query = query
    nlu_confidence = 0.0
    planned_tools: list[str] = []

    def emit_token(token: str) -> str:
        nonlocal first_token_latency_ms
        if first_token_latency_ms is None:
            first_token_latency_ms = (time.perf_counter() - started) * 1000
            tracer.emit("answer", "first_token", latency_ms=first_token_latency_ms)
        answer_parts.append(token)
        return _sse({"type": "token", "content": token})

    yield _sse({"conversation_id": conversation_id, "run_id": run_id, "persona": persona})

    if not is_safe_query(query):
        yield _progress("Yêu cầu không phù hợp để hỗ trợ", step="safety", tracer=tracer)
        blocked = "Mình chưa thể hỗ trợ nội dung này vì lý do an toàn."
        yield emit_token(blocked)
        intent = "blocked"
    else:
        yield _progress("Đang nạp ngữ cảnh hội thoại", step="context", tracer=tracer)
        assistant_context = build_assistant_context(db, actor_id=actor_id, conversation_id=conversation_id, persona_id=persona)

        yield _progress("Đang xác định ý định", step="nlu", tracer=tracer)
        nlu_result = analyze_intent(
            query,
            persona,
            recent_turns=assistant_context.recent_turns,
            memories=assistant_context.memories,
            profile=assistant_context.profile,
        )
        intent = nlu_result.intent
        rewritten_query = nlu_result.rewritten_query
        nlu_confidence = nlu_result.confidence
        tracer.emit("nlu", "done", intent=intent, confidence=nlu_confidence, rewritten_query=rewritten_query)
        yield _sse({"type": "intent", "step": "intent", "intent": intent, "persona": persona})

        yield _progress("Đang lập kế hoạch công cụ", step="planner", tracer=tracer)
        planned_tools = plan_tools(intent, persona)
        tracer.emit("planner", "done", intent=intent, planned_tools=planned_tools)

        if nlu_result.suggested_answer:
            yield _progress("Đang tổng hợp câu trả lời", step="compose", tracer=tracer)
            for token in _text_chunks(nlu_result.suggested_answer):
                yield emit_token(token)
        else:
            for tool_name in planned_tools:
                tool_started = time.perf_counter()
                if tool_name == "rag":
                    tool_output: dict | None = None
                    yield _progress("Đang chuẩn bị truy xuất tri thức", step="tool", tracer=tracer, tool_name=tool_name)
                    for event in stream_answer_from_knowledge(
                        rewritten_query,
                        db=db,
                        persona_id=persona,
                        intent="rag",
                        run_id=run_id if tracer.run_row_enabled else None,
                    ):
                        event_name = event.get("event")
                        data = event.get("data")
                        if event_name == "progress" and isinstance(data, dict):
                            yield _progress(str(data.get("message") or "Đang xử lý tài liệu"), step=str(data.get("step") or "rag"), tracer=tracer)
                        elif event_name == "sources" and isinstance(data, dict):
                            stream_sources = data.get("sources")
                            yield _sse({"type": "sources", "sources": stream_sources, **{k: v for k, v in data.items() if k != "sources"}})
                        elif event_name == "token":
                            yield emit_token(str(data or ""))
                        elif event_name == "answer" and isinstance(data, dict):
                            tool_output = data
                        elif event_name == "error" and isinstance(data, dict):
                            yield emit_token(str(data.get("message") or "Có lỗi khi truy xuất tài liệu."))
                    output = tool_output or {"answer": "".join(answer_parts), "sources": stream_sources or []}
                    tool_results.append({"tool_name": tool_name, "input": {"query": rewritten_query}, "output": output})
                    tracer.emit(
                        "tool",
                        "done",
                        tool_name=tool_name,
                        latency_ms=(time.perf_counter() - tool_started) * 1000,
                        output_keys=list(output.keys()),
                        retrieved_count=output.get("retrieved_count"),
                        reranked_count=output.get("reranked_count"),
                        source_count=len(output.get("sources") or []),
                        top_sources=_top_sources(output),
                    )
                else:
                    yield _progress(f"Đang gọi công cụ {tool_name}", step="tool", tracer=tracer, tool_name=tool_name)
                    try:
                        tool_result = execute_tool(
                            tool_name,
                            persona=persona,
                            query=rewritten_query,
                            actor_id=actor_id,
                            db=db,
                            lat=req.lat,
                            lng=req.lng,
                            address=req.address,
                            budget_vnd=req.budget_vnd,
                            run_id=run_id if tracer.run_row_enabled else None,
                        )
                    except (ToolPermissionError, ToolExecutionError) as exc:
                        tool_result = {"tool_name": tool_name, "error": str(exc)}
                    tool_results.append(tool_result)

            if planned_tools and planned_tools != ["rag"]:
                yield _progress("Đang tổng hợp kết quả công cụ", step="compose", tracer=tracer)
                composed = compose_response(persona=persona, intent=intent, tool_results=tool_results)
                for token in _text_chunks(composed):
                    yield emit_token(token)

    answer = "".join(answer_parts)
    completion_latency_ms = (time.perf_counter() - started) * 1000
    display_latency_ms = first_token_latency_ms if first_token_latency_ms is not None else completion_latency_ms
    metrics = {
        "nlu_confidence": nlu_confidence,
        "rewritten_query": rewritten_query,
        "nlu_suggested_answer": False,
        "planned_tools": planned_tools,
        "time_to_first_token_ms": display_latency_ms,
        "completion_latency_ms": completion_latency_ms,
        "total_latency_ms": display_latency_ms,
        "active_layers": tracer.active_layers(),
        "pipeline_trace": tracer.summary(),
    }
    tracer.emit("api", "run_done", total_latency_ms=display_latency_ms, completion_latency_ms=completion_latency_ms)
    tracer.finish_run(intent=intent, status="completed", latency_ms=display_latency_ms)

    assistant_message = save_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        metadata={"run_id": run_id, "persona": persona, "metrics": metrics, "tool_results": tool_results},
    )
    metrics["message_id"] = assistant_message.id
    yield _sse({"message_id": assistant_message.id})
    yield _sse({"type": "metrics", "metrics": metrics, "tool_results": tool_results})
    yield _sse("[DONE]")


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

    return StreamingResponse(
        _stream_chat(req=req, db=db, actor_id=actor_id, conversation_id=conversation.id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
