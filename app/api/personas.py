from __future__ import annotations

from fastapi import APIRouter

from app.assistant.personas import list_persona_configs


router = APIRouter()


@router.get("")
def list_personas() -> list[dict[str, object]]:
    return [
        {
            "id": config.persona_id.value,
            "display_name": config.display_name,
            "prompt_key": config.prompt_key,
            "allowed_tools": list(config.allowed_tools),
            "memory_scopes": list(config.memory_scopes),
            "data_scopes": list(config.data_scopes),
            "requires_auth": config.requires_auth,
        }
        for config in list_persona_configs()
    ]
