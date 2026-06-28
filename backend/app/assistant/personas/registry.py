from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AssistantPersona(str, Enum):
    CUSTOMER = "customer"
    DRIVER = "driver"
    MERCHANT = "merchant"
    OPERATOR = "operator"
    EXECUTIVE = "executive"


@dataclass(frozen=True)
class PersonaConfig:
    persona_id: AssistantPersona
    display_name: str
    prompt_key: str
    allowed_tools: tuple[str, ...]
    memory_scopes: tuple[str, ...]
    data_scopes: tuple[str, ...]
    requires_auth: bool = False


from app.assistant.personas.customer_persona import CUSTOMER_PERSONA
from app.assistant.personas.driver_persona import DRIVER_PERSONA
from app.assistant.personas.executive_persona import EXECUTIVE_PERSONA
from app.assistant.personas.merchant_persona import MERCHANT_PERSONA
from app.assistant.personas.operator_persona import OPERATOR_PERSONA


PERSONA_REGISTRY: dict[AssistantPersona, PersonaConfig] = {
    CUSTOMER_PERSONA.persona_id: CUSTOMER_PERSONA,
    DRIVER_PERSONA.persona_id: DRIVER_PERSONA,
    MERCHANT_PERSONA.persona_id: MERCHANT_PERSONA,
    OPERATOR_PERSONA.persona_id: OPERATOR_PERSONA,
    EXECUTIVE_PERSONA.persona_id: EXECUTIVE_PERSONA,
}


def normalize_persona_id(persona_id: str | AssistantPersona | None) -> AssistantPersona:
    if isinstance(persona_id, AssistantPersona):
        return persona_id
    if not persona_id:
        return AssistantPersona.CUSTOMER
    try:
        return AssistantPersona(str(persona_id).strip().lower())
    except ValueError:
        return AssistantPersona.CUSTOMER


def get_persona_config(persona_id: str | AssistantPersona | None) -> PersonaConfig:
    return PERSONA_REGISTRY[normalize_persona_id(persona_id)]


def list_persona_configs() -> list[PersonaConfig]:
    return list(PERSONA_REGISTRY.values())


def can_use_tool(persona_id: str | AssistantPersona | None, tool_name: str) -> bool:
    config = get_persona_config(persona_id)
    return tool_name in config.allowed_tools
