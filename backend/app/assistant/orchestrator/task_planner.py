from __future__ import annotations


def plan_tools(intent: str, persona: str) -> list[str]:
    if intent in {"small_talk", "missing_info", "sensitive"}:
        return []
    if intent == "food_recommendation":
        return ["food"]
    if intent == "ride_support":
        return ["ride"]
    if intent == "driver_support":
        return ["ride_status", "charging", "demand_heatmap"]
    if intent == "merchant_analytics":
        return ["merchant_analytics", "menu_analysis", "review_analysis"]
    if intent == "operations_monitoring":
        return ["fleet_monitor", "revenue_diagnostics", "fraud_detection"]
    if intent == "executive_insight":
        return ["bi_analysis", "forecast_simulation"]
    if persona == "driver":
        return ["ride_status", "charging", "demand_heatmap"]
    if persona == "merchant":
        return ["merchant_analytics", "menu_analysis", "review_analysis"]
    if persona == "operator":
        return ["fleet_monitor", "revenue_diagnostics", "fraud_detection"]
    if persona == "executive":
        return ["bi_analysis", "forecast_simulation"]
    return ["rag"]
