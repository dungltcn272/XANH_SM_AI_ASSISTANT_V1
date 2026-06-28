from __future__ import annotations


def plan_tools(intent: str, persona: str) -> list[str]:
    if intent == "food_recommendation":
        return ["food"]
    if persona == "driver":
        return ["ride_status", "charging", "demand_heatmap"]
    if persona == "merchant":
        return ["merchant_analytics", "menu_analysis", "review_analysis"]
    if persona == "operator":
        return ["fleet_monitor", "revenue_diagnostics", "fraud_detection"]
    if persona == "executive":
        return ["bi_analysis", "forecast_simulation"]
    if intent == "ride_support":
        return ["ride"]
    return ["rag"]
