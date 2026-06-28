from dataclasses import dataclass


@dataclass(frozen=True)
class IntentRoute:
    intent: str
    capability: str
    requires_tool: bool = False


def route_intent(intent: str) -> IntentRoute:
    if intent == "food_recommendation":
        return IntentRoute(intent=intent, capability="food", requires_tool=True)
    if intent == "ride_support":
        return IntentRoute(intent=intent, capability="ride", requires_tool=True)
    if intent == "driver_support":
        return IntentRoute(intent=intent, capability="driver", requires_tool=True)
    if intent == "merchant_analytics":
        return IntentRoute(intent=intent, capability="merchant", requires_tool=True)
    if intent == "operations_monitoring":
        return IntentRoute(intent=intent, capability="operator", requires_tool=True)
    if intent == "executive_insight":
        return IntentRoute(intent=intent, capability="executive", requires_tool=True)
    if intent in {"small_talk", "missing_info", "sensitive"}:
        return IntentRoute(intent=intent, capability="direct_response")
    return IntentRoute(intent=intent or "rag", capability="rag", requires_tool=True)
