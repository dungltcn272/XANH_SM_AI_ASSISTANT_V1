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


PERSONA_REGISTRY: dict[AssistantPersona, PersonaConfig] = {
    AssistantPersona.CUSTOMER: PersonaConfig(
        persona_id=AssistantPersona.CUSTOMER,
        display_name="Customer AI Assistant",
        prompt_key="customer_persona",
        allowed_tools=("rag", "food", "ride", "travel", "commerce", "payment_stub"),
        memory_scopes=("general", "food", "ride", "travel"),
        data_scopes=("public", "customer"),
    ),
    AssistantPersona.DRIVER: PersonaConfig(
        persona_id=AssistantPersona.DRIVER,
        display_name="Driver Copilot",
        prompt_key="driver_persona",
        allowed_tools=("rag_driver", "ride_status", "map", "charging", "demand_heatmap"),
        memory_scopes=("driver", "ride", "charging"),
        data_scopes=("driver", "public"),
        requires_auth=True,
    ),
    AssistantPersona.MERCHANT: PersonaConfig(
        persona_id=AssistantPersona.MERCHANT,
        display_name="Merchant Copilot",
        prompt_key="merchant_persona",
        allowed_tools=("merchant_analytics", "menu_analysis", "review_analysis", "promotion_advisor", "menu_ocr"),
        memory_scopes=("merchant", "menu", "promotion", "review"),
        data_scopes=("merchant", "public"),
        requires_auth=True,
    ),
    AssistantPersona.OPERATOR: PersonaConfig(
        persona_id=AssistantPersona.OPERATOR,
        display_name="Operator Copilot",
        prompt_key="operator_persona",
        allowed_tools=("fleet_monitor", "revenue_diagnostics", "fraud_detection", "incident_monitor"),
        memory_scopes=("ops", "fleet", "incident", "fraud"),
        data_scopes=("operator", "ops", "public"),
        requires_auth=True,
    ),
    AssistantPersona.EXECUTIVE: PersonaConfig(
        persona_id=AssistantPersona.EXECUTIVE,
        display_name="Executive AI",
        prompt_key="executive_persona",
        allowed_tools=("bi_analysis", "forecast_simulation", "churn_prediction", "expansion_advisor"),
        memory_scopes=("executive", "bi", "forecast", "strategy"),
        data_scopes=("executive", "bi", "public"),
        requires_auth=True,
    ),
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
