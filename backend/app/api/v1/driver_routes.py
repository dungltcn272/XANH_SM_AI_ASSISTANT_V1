from fastapi import APIRouter

from app.domains.driver_copilot.charging_station_service import nearby_charging_stations
from app.domains.driver_copilot.demand_prediction import demand_heatmap
from app.domains.driver_copilot.driver_assistant_service import driver_summary
from app.schemas.response import CapabilityResponse


router = APIRouter()


@router.get("/capabilities", response_model=CapabilityResponse)
def driver_capabilities() -> CapabilityResponse:
    return CapabilityResponse(
        persona="driver",
        tools=["rag_driver", "ride_status", "map", "charging", "demand_heatmap"],
        demo_queries=["Khách của tôi đang ở đâu?", "Trạm sạc gần nhất ở đâu?", "Khu nào đang nhiều nhu cầu?"],
    )


@router.get("/status")
def driver_status() -> dict:
    return driver_summary()


@router.get("/charging-stations")
def charging_stations() -> dict:
    return {"stations": nearby_charging_stations()}


@router.get("/demand-heatmap")
def demand() -> dict:
    return demand_heatmap()
