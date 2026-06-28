from fastapi import APIRouter

from app.domains.operator_copilot.fleet_monitor import fleet_metrics
from app.domains.operator_copilot.fraud_detection import fraud_signals
from app.domains.operator_copilot.incident_monitor import incident_summary
from app.domains.operator_copilot.revenue_diagnostics import revenue_diagnostics
from app.schemas.response import CapabilityResponse


router = APIRouter()


@router.get("/capabilities", response_model=CapabilityResponse)
def operator_capabilities() -> CapabilityResponse:
    return CapabilityResponse(
        persona="operator",
        tools=["fleet_monitor", "revenue_diagnostics", "fraud_detection", "incident_monitor"],
        demo_queries=["Có bao nhiêu tài xế online?", "Doanh thu khu vực HCM thế nào?", "Có tín hiệu gian lận nào không?"],
    )


@router.get("/metrics")
def metrics() -> dict:
    return {"fleet": fleet_metrics(), "revenue": revenue_diagnostics(), "fraud": fraud_signals(), "incidents": incident_summary()}
