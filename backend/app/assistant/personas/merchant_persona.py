from app.assistant.personas.registry import AssistantPersona, PersonaConfig


MERCHANT_PERSONA = PersonaConfig(
    persona_id=AssistantPersona.MERCHANT,
    display_name="Merchant Copilot",
    prompt_key="merchant_persona",
    allowed_tools=("merchant_analytics", "menu_analysis", "review_analysis", "promotion_advisor", "menu_ocr"),
    memory_scopes=("merchant", "menu", "promotion", "review"),
    data_scopes=("merchant", "public"),
    requires_auth=True,
)
