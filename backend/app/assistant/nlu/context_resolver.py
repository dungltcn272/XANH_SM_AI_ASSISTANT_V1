from __future__ import annotations


def resolve_context(query: str, recent_turns: list[dict[str, str]]) -> dict:
    return {"has_history": bool(recent_turns), "query": query}
