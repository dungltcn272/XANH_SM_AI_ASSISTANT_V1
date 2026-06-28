from app.assistant.personas.registry import AssistantPersona, PersonaConfig


CUSTOMER_PERSONA = PersonaConfig(
    persona_id=AssistantPersona.CUSTOMER,
    display_name="Customer AI Assistant",
    prompt_key="customer_persona",
    allowed_tools=("rag", "food", "ride", "travel", "commerce", "payment_stub"),
    memory_scopes=("general", "food", "ride", "travel"),
    data_scopes=("public", "customer"),
)
