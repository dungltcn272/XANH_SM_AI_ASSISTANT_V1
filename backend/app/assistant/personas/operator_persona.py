from app.assistant.personas.registry import AssistantPersona, PersonaConfig


OPERATOR_PERSONA = PersonaConfig(
    persona_id=AssistantPersona.OPERATOR,
    display_name="Operator Copilot",
    prompt_key="operator_persona",
    allowed_tools=("fleet_monitor", "revenue_diagnostics", "fraud_detection", "incident_monitor"),
    memory_scopes=("ops", "fleet", "incident", "fraud"),
    data_scopes=("operator", "ops", "public"),
    requires_auth=True,
)
