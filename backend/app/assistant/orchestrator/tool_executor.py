from __future__ import annotations

from sqlalchemy.orm import Session

from app.assistant.policies.permission_guard import assert_tool_allowed
from app.domains.driver_copilot.charging_station_service import nearby_charging_stations
from app.domains.driver_copilot.demand_prediction import demand_heatmap
from app.domains.driver_copilot.trip_status_service import current_trip_status
from app.domains.executive_copilot.bi_analysis import bi_summary
from app.domains.executive_copilot.forecast_simulation import voucher_simulation
from app.domains.food.recommendation_service import recommend_food
from app.domains.merchant_copilot.menu_analysis import menu_optimization
from app.domains.merchant_copilot.revenue_analysis import revenue_summary
from app.domains.merchant_copilot.review_analysis import review_sentiment
from app.domains.operator_copilot.fleet_monitor import fleet_metrics
from app.domains.operator_copilot.fraud_detection import fraud_signals
from app.domains.operator_copilot.revenue_diagnostics import revenue_diagnostics
from app.domains.ride.booking_service import ride_support_from_query
from app.assistant.orchestrator.rag_answerer import answer_from_knowledge


class ToolPermissionError(PermissionError):
    pass


def execute_tool(
    tool_name: str,
    *,
    persona: str,
    query: str,
    actor_id: str | None = None,
    db: Session | None = None,
    lat: float | None = None,
    lng: float | None = None,
    address: str | None = None,
    budget_vnd: int | None = None,
) -> dict:
    try:
        assert_tool_allowed(persona, tool_name)
    except PermissionError as exc:
        raise ToolPermissionError(str(exc)) from exc

    if tool_name in {"rag", "rag_driver"}:
        return {"tool_name": tool_name, "output": answer_from_knowledge(query, db=db)}
    if tool_name == "food":
        return {
            "tool_name": tool_name,
            "output": recommend_food(query, db=db, actor_id=actor_id, lat=lat, lng=lng, address=address, budget_vnd=budget_vnd),
        }
    if tool_name in {"ride", "ride_status"}:
        output = current_trip_status() if tool_name == "ride_status" else ride_support_from_query(query, db=db, actor_id=actor_id)
        return {"tool_name": tool_name, "output": output}
    if tool_name == "charging":
        return {"tool_name": tool_name, "output": {"stations": nearby_charging_stations()}}
    if tool_name == "demand_heatmap":
        return {"tool_name": tool_name, "output": demand_heatmap()}
    if tool_name == "merchant_analytics":
        return {"tool_name": tool_name, "output": revenue_summary()}
    if tool_name == "menu_analysis":
        return {"tool_name": tool_name, "output": menu_optimization()}
    if tool_name == "review_analysis":
        return {"tool_name": tool_name, "output": review_sentiment()}
    if tool_name == "fleet_monitor":
        return {"tool_name": tool_name, "output": fleet_metrics()}
    if tool_name == "revenue_diagnostics":
        return {"tool_name": tool_name, "output": revenue_diagnostics()}
    if tool_name == "fraud_detection":
        return {"tool_name": tool_name, "output": fraud_signals()}
    if tool_name == "bi_analysis":
        return {"tool_name": tool_name, "output": bi_summary()}
    if tool_name == "forecast_simulation":
        return {"tool_name": tool_name, "output": voucher_simulation()}
    return {"tool_name": tool_name, "output": {"status": "not_implemented"}}
