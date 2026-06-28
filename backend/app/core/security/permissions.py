from app.assistant.personas import get_persona_config


def require_persona_access(persona_id: str, tool_name: str) -> bool:
    persona_config = get_persona_config(persona_id)
    return tool_name in persona_config.allowed_tools
