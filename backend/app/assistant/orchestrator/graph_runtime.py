from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AssistantState:
    query: str
    persona: str = "customer"
    conversation_id: str | None = None
    actor_id: str | None = None
    intent: str | None = None
    rewritten_query: str | None = None
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


def mark_step(state: AssistantState, step: str) -> AssistantState:
    state.metrics.setdefault("steps", []).append(step)
    return state
