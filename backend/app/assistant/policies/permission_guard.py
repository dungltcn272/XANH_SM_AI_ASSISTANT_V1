from __future__ import annotations

from app.assistant.personas import can_use_tool


def assert_tool_allowed(persona_id: str, tool_name: str) -> None:
    if not can_use_tool(persona_id, tool_name):
        raise PermissionError(f"Persona {persona_id} cannot use tool {tool_name}")
