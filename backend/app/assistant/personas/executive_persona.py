from app.assistant.personas.registry import AssistantPersona, PersonaConfig


EXECUTIVE_PERSONA = PersonaConfig(
    persona_id=AssistantPersona.EXECUTIVE,
    display_name="Executive AI",
    prompt_key="executive_persona",
    allowed_tools=("bi_analysis", "forecast_simulation", "churn_prediction", "expansion_advisor"),
    memory_scopes=("executive", "bi", "forecast", "strategy"),
    data_scopes=("executive", "bi", "public"),
    requires_auth=True,
)
