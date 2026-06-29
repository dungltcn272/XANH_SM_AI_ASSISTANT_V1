from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.assistant.memory.context_builder import build_assistant_context
from app.assistant.nlu import analyze_intent
from app.assistant.orchestrator.graph_runtime import AssistantState, mark_step
from app.assistant.orchestrator.response_composer import compose_response
from app.assistant.orchestrator.task_planner import plan_tools
from app.assistant.orchestrator.tool_executor import ToolExecutionError, ToolPermissionError, execute_tool
from app.assistant.personas import get_persona_config
from app.assistant.policies.safety_guard import is_safe_query
from app.core.logging.pipeline_trace import PipelineTracer


class XanhSMAssistantOrchestrator:
    def run(
        self,
        *,
        query: str,
        persona: str = "customer",
        actor_id: str | None = None,
        conversation_id: str | None = None,
        db: Session | None = None,
        lat: float | None = None,
        lng: float | None = None,
        address: str | None = None,
        budget_vnd: int | None = None,
    ) -> dict:
        started = time.perf_counter()
        run_id = f"run_{uuid.uuid4().hex}"
        persona_config = get_persona_config(persona)
        state = AssistantState(query=query, persona=persona_config.persona_id.value, actor_id=actor_id, conversation_id=conversation_id)
        tracer = PipelineTracer(run_id=run_id, conversation_id=conversation_id, persona_id=state.persona, db=db)
        tracer.start_run(actor_id=actor_id)
        tracer.emit("api", "run_start", query=query, actor_id=actor_id)

        if not is_safe_query(query):
            tracer.emit("safety", "blocked", level="WARNING")
            blocked_latency_ms = (time.perf_counter() - started) * 1000
            tracer.finish_run(intent="blocked", status="blocked", latency_ms=blocked_latency_ms)
            return {
                "run_id": run_id,
                "persona": state.persona,
                "intent": "blocked",
                "answer": "Mình chưa thể hỗ trợ nội dung này vì lý do an toàn.",
                "tool_results": [],
                "metrics": {
                    "total_latency_ms": blocked_latency_ms,
                    "active_layers": tracer.active_layers(),
                    "pipeline_trace": tracer.summary(),
                },
            }

        mark_step(state, "context")
        tracer.emit("context", "start")
        assistant_context = None
        if db is not None:
            assistant_context = build_assistant_context(db, actor_id=actor_id, conversation_id=conversation_id, persona_id=state.persona)
        tracer.emit(
            "context",
            "done",
            recent_turns=len(assistant_context.recent_turns) if assistant_context else 0,
            memories=len(assistant_context.memories) if assistant_context else 0,
        )

        mark_step(state, "intent")
        tracer.emit("nlu", "start", query=query, model="rule_or_llm")
        nlu_result = analyze_intent(
            query,
            state.persona,
            recent_turns=assistant_context.recent_turns if assistant_context else None,
            memories=assistant_context.memories if assistant_context else None,
            profile=assistant_context.profile if assistant_context else None,
        )
        state.intent = nlu_result.intent
        state.rewritten_query = nlu_result.rewritten_query
        tracer.emit(
            "nlu",
            "done",
            intent=state.intent,
            confidence=nlu_result.confidence,
            rewritten_query=state.rewritten_query,
            direct_answer=bool(nlu_result.suggested_answer),
        )

        mark_step(state, "plan")
        planned_tools = plan_tools(state.intent, state.persona)
        tracer.emit("planner", "done", intent=state.intent, planned_tools=planned_tools)

        if nlu_result.suggested_answer:
            answer = nlu_result.suggested_answer
            tracer.emit("direct_response", "used", reason=state.intent)
        else:
            for tool_name in planned_tools:
                tool_started = time.perf_counter()
                tracer.emit("tool", "start", tool_name=tool_name)
                try:
                    tool_result = execute_tool(
                        tool_name,
                        persona=state.persona,
                        query=state.rewritten_query,
                        actor_id=actor_id,
                        db=db,
                        lat=lat,
                        lng=lng,
                        address=address,
                        budget_vnd=budget_vnd,
                        run_id=run_id if tracer.run_row_enabled else None,
                    )
                    state.tool_results.append(tool_result)
                    output = tool_result.get("output") if isinstance(tool_result, dict) else None
                    sources = output.get("sources") if isinstance(output, dict) else None
                    top_sources = []
                    if isinstance(sources, list):
                        top_sources = [
                            {
                                "chunk_id": source.get("chunk_id"),
                                "section": source.get("section"),
                                "score": source.get("score"),
                                "retrieval_source": source.get("retrieval_source"),
                            }
                            for source in sources[:3]
                            if isinstance(source, dict)
                        ]
                    tracer.emit(
                        "tool",
                        "done",
                        tool_name=tool_name,
                        latency_ms=(time.perf_counter() - tool_started) * 1000,
                        output_keys=list(output.keys()) if isinstance(output, dict) else [],
                        retrieved_count=output.get("retrieved_count") if isinstance(output, dict) else None,
                        reranked_count=output.get("reranked_count") if isinstance(output, dict) else None,
                        source_count=len(sources) if isinstance(sources, list) else None,
                        top_sources=top_sources,
                    )
                except ToolPermissionError as exc:
                    state.tool_results.append({"tool_name": tool_name, "error": str(exc)})
                    tracer.emit("tool", "permission_denied", level="WARNING", tool_name=tool_name, error=str(exc))
                except ToolExecutionError as exc:
                    state.tool_results.append({"tool_name": tool_name, "error": str(exc)})
                    tracer.emit("tool", "error", level="ERROR", tool_name=tool_name, error=str(exc))

            tracer.emit("compose", "start", tool_count=len(state.tool_results))
            answer = compose_response(persona=state.persona, intent=state.intent, tool_results=state.tool_results)
            tracer.emit("compose", "done", answer_chars=len(answer))

        mark_step(state, "compose")
        state.metrics["nlu_confidence"] = nlu_result.confidence
        state.metrics["rewritten_query"] = state.rewritten_query
        state.metrics["nlu_suggested_answer"] = bool(nlu_result.suggested_answer)
        state.metrics["total_latency_ms"] = (time.perf_counter() - started) * 1000
        state.metrics["planned_tools"] = planned_tools
        tracer.emit("api", "run_done", total_latency_ms=state.metrics["total_latency_ms"])
        tracer.finish_run(intent=state.intent, status="completed", latency_ms=state.metrics["total_latency_ms"])
        state.metrics["active_layers"] = tracer.active_layers()
        state.metrics["pipeline_trace"] = tracer.summary()

        return {
            "run_id": run_id,
            "persona": state.persona,
            "intent": state.intent,
            "answer": answer,
            "tool_results": state.tool_results,
            "metrics": state.metrics,
        }

    def stream(self, *, query: str, persona: str = "customer", actor_id: str | None = None, conversation_id: str | None = None, db: Session | None = None) -> Iterator[str]:
        result = self.run(query=query, persona=persona, actor_id=actor_id, conversation_id=conversation_id, db=db)
        yield f"data: {json.dumps({'conversation_id': conversation_id, 'run_id': result['run_id'], 'persona': result['persona']}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'step': 'intent', 'intent': result['intent'], 'persona': result['persona']}, ensure_ascii=False)}\n\n"
        for line in result["answer"].splitlines():
            yield f"data: {line}\n\n"
        yield f"data: {json.dumps({'metrics': result['metrics'], 'tool_results': result['tool_results']}, ensure_ascii=False, default=str)}\n\n"
        yield "data: [DONE]\n\n"
