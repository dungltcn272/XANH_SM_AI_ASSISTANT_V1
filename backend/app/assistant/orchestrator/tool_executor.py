from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.assistant.orchestrator.rag_answerer import answer_from_knowledge
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
from app.domains.ride.booking_service import create_booking, ride_support_from_query
from app.domains.ride.schemas import RideBookingRequest, RideLocation
from app.tools import get_tool


class ToolPermissionError(PermissionError):
    pass


class ToolExecutionError(RuntimeError):
    pass


def _tool_envelope(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    spec = get_tool(tool_name)
    if spec is None:
        return {"tool_name": tool_name, **payload}
    filtered = payload
    if spec.args_schema is not None:
        allowed = set(spec.args_schema.model_fields)
        filtered = {key: value for key, value in payload.items() if key in allowed and value is not None}
    if spec.langchain_tool is not None:
        result = spec.langchain_tool.invoke(filtered)
        return result if isinstance(result, dict) else {"tool_name": tool_name, "result": result}
    if spec.args_schema is not None:
        validated = spec.args_schema.model_validate(filtered)
        return {"tool_name": tool_name, **validated.model_dump()}
    return {"tool_name": tool_name, **filtered}


def _rag(envelope: dict, *, persona: str, db: Session | None, **_: Any) -> dict:
    return answer_from_knowledge(envelope.get("query") or "", db=db, persona_id=persona, intent="rag", top_k=envelope.get("top_k"))


def _food(envelope: dict, *, actor_id: str | None, db: Session | None, **_: Any) -> dict:
    return recommend_food(
        envelope.get("query") or "",
        db=db,
        actor_id=actor_id,
        lat=envelope.get("lat"),
        lng=envelope.get("lng"),
        address=envelope.get("address"),
        budget_vnd=envelope.get("budget_vnd"),
        limit=envelope.get("limit") or 8,
    )


def _ride(envelope: dict, *, actor_id: str | None, db: Session | None, **_: Any) -> dict:
    pickup = envelope.get("pickup")
    dropoff = envelope.get("dropoff")
    if pickup and dropoff:
        return create_booking(
            RideBookingRequest(
                pickup=RideLocation(address=pickup),
                dropoff=RideLocation(address=dropoff),
                service_type=envelope.get("service_type") or "xanh_car",
                confirm=bool(envelope.get("confirm")),
            ),
            db=db,
            actor_id=actor_id,
        )
    return ride_support_from_query(envelope.get("query") or "", db=db, actor_id=actor_id)


def _ride_status(envelope: dict, **_: Any) -> dict:
    return current_trip_status()


def _charging(envelope: dict, **_: Any) -> dict:
    return {"stations": nearby_charging_stations()}


def _demand_heatmap(envelope: dict, **_: Any) -> dict:
    return demand_heatmap()


def _merchant_analytics(envelope: dict, **_: Any) -> dict:
    return revenue_summary()


def _menu_analysis(envelope: dict, **_: Any) -> dict:
    return menu_optimization()


def _review_analysis(envelope: dict, **_: Any) -> dict:
    return review_sentiment()


def _fleet_monitor(envelope: dict, **_: Any) -> dict:
    return fleet_metrics()


def _revenue_diagnostics(envelope: dict, **_: Any) -> dict:
    return revenue_diagnostics()


def _fraud_detection(envelope: dict, **_: Any) -> dict:
    return fraud_signals()


def _bi_analysis(envelope: dict, **_: Any) -> dict:
    return bi_summary()


def _forecast_simulation(envelope: dict, **_: Any) -> dict:
    return voucher_simulation()


_DISPATCH: dict[str, Callable[..., dict]] = {
    "rag": _rag,
    "rag_driver": _rag,
    "food": _food,
    "ride": _ride,
    "ride_status": _ride_status,
    "charging": _charging,
    "demand_heatmap": _demand_heatmap,
    "merchant_analytics": _merchant_analytics,
    "menu_analysis": _menu_analysis,
    "review_analysis": _review_analysis,
    "fleet_monitor": _fleet_monitor,
    "revenue_diagnostics": _revenue_diagnostics,
    "fraud_detection": _fraud_detection,
    "bi_analysis": _bi_analysis,
    "forecast_simulation": _forecast_simulation,
}


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

    envelope = _tool_envelope(
        tool_name,
        {
            "query": query,
            "lat": lat,
            "lng": lng,
            "address": address,
            "budget_vnd": budget_vnd,
        },
    )
    handler = _DISPATCH.get(tool_name)
    if handler is None:
        return {"tool_name": tool_name, "output": {"status": "not_implemented", "envelope": envelope}}
    try:
        output = handler(envelope, persona=persona, actor_id=actor_id, db=db)
    except Exception as exc:
        raise ToolExecutionError(f"Tool {tool_name} failed: {exc}") from exc
    return {"tool_name": tool_name, "input": envelope, "output": output}
