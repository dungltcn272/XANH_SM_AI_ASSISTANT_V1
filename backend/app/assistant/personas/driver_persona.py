from app.assistant.personas.registry import AssistantPersona, PersonaConfig


DRIVER_PERSONA = PersonaConfig(
    persona_id=AssistantPersona.DRIVER,
    display_name="Driver Copilot",
    prompt_key="driver_persona",
    allowed_tools=("rag_driver", "ride_status", "map", "charging", "demand_heatmap"),
    memory_scopes=("driver", "ride", "charging"),
    data_scopes=("driver", "public"),
    requires_auth=True,
)
