from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.assistant.nlu import classify_intent, rewrite_query
from app.assistant.orchestrator.graph_runtime import AssistantState, mark_step
from app.assistant.orchestrator.response_composer import compose_response
from app.assistant.orchestrator.task_planner import plan_tools
from app.assistant.orchestrator.tool_executor import ToolPermissionError, execute_tool
from app.assistant.personas import get_persona_config
from app.assistant.policies.hallucination_guard import add_demo_disclaimer
from app.assistant.policies.safety_guard import is_safe_query


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
        persona_config = get_persona_config(persona)
        state = AssistantState(query=query, persona=persona_config.persona_id.value, actor_id=actor_id, conversation_id=conversation_id)

        if not is_safe_query(query):
            return {
                "run_id": f"run_{uuid.uuid4().hex}",
                "persona": state.persona,
                "intent": "blocked",
                "answer": "Mình chưa thể hỗ trợ nội dung này vì lý do an toàn.",
                "tool_results": [],
                "metrics": {"total_latency_ms": (time.perf_counter() - started) * 1000},
            }

        mark_step(state, "rewrite")
        state.rewritten_query = rewrite_query(query)
        mark_step(state, "intent")
        state.intent = classify_intent(state.rewritten_query, state.persona)
        planned_tools = plan_tools(state.intent, state.persona)
        mark_step(state, "plan")

        for tool_name in planned_tools:
            try:
                state.tool_results.append(
                    execute_tool(
                        tool_name,
                        persona=state.persona,
                        query=state.rewritten_query,
                        actor_id=actor_id,
                        db=db,
                        lat=lat,
                        lng=lng,
                        address=address,
                        budget_vnd=budget_vnd,
                    )
                )
            except ToolPermissionError as exc:
                state.tool_results.append({"tool_name": tool_name, "error": str(exc)})

        mark_step(state, "compose")
        answer = add_demo_disclaimer(compose_response(persona=state.persona, intent=state.intent, tool_results=state.tool_results))
        state.metrics["total_latency_ms"] = (time.perf_counter() - started) * 1000
        state.metrics["planned_tools"] = planned_tools

        return {
            "run_id": f"run_{uuid.uuid4().hex}",
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
