from dataclasses import dataclass


@dataclass(frozen=True)
class IntentRoute:
    intent: str
    capability: str
    requires_tool: bool = False


def route_intent(intent: str) -> IntentRoute:
    if intent == "food_recommendation":
        return IntentRoute(intent=intent, capability="food", requires_tool=True)
    if intent in {"small-talk", "missing_info", "sensitive"}:
        return IntentRoute(intent=intent, capability="direct_response")
    return IntentRoute(intent=intent or "rag", capability="rag", requires_tool=True)
