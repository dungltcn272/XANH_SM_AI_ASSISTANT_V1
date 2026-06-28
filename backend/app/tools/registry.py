from app.assistant.personas import can_use_tool, list_persona_configs
from app.tools.base_tool import ToolSpec

_TOOL_REGISTRY: dict[str, ToolSpec] = {}


def register_tool(tool: ToolSpec) -> ToolSpec:
    _TOOL_REGISTRY[tool.name] = tool
    return tool


def get_tool(tool_name: str) -> ToolSpec | None:
    return _TOOL_REGISTRY.get(tool_name)


def list_tools_for_persona(persona_id: str) -> list[ToolSpec]:
    return [tool for tool in _TOOL_REGISTRY.values() if can_use_tool(persona_id, tool.name)]


def list_persona_tool_matrix() -> dict[str, list[str]]:
    return {
        persona.persona_id.value: [
            tool.name for tool in _TOOL_REGISTRY.values() if can_use_tool(persona.persona_id.value, tool.name)
        ]
        for persona in list_persona_configs()
    }
