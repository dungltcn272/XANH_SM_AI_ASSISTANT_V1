from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool


class RideToolInput(BaseModel):
    query: str = Field(..., description="Câu yêu cầu đặt xe hoặc ước tính chuyến đi.")
    pickup: str | None = Field(default=None, description="Điểm đón nếu đã trích xuất được.")
    dropoff: str | None = Field(default=None, description="Điểm đến nếu đã trích xuất được.")
    service_type: str = Field(default="xanh_car", pattern="^(xanh_car|xanh_bike|premium)$")
    confirm: bool = Field(default=False, description="True nếu người dùng đã xác nhận muốn đặt.")


class RideStatusToolInput(BaseModel):
    trip_id: str | None = Field(default=None, description="Mã chuyến nếu người dùng hỏi chuyến cụ thể.")


@tool("ride", args_schema=RideToolInput, description="Estimate or prepare a Xanh SM ride booking from pickup to dropoff.")
def ride_langchain_tool(
    query: str,
    pickup: str | None = None,
    dropoff: str | None = None,
    service_type: str = "xanh_car",
    confirm: bool = False,
) -> dict:
    """Return a ride request envelope for the orchestrator to execute with DB context."""
    return {
        "tool_name": "ride",
        "query": query,
        "pickup": pickup,
        "dropoff": dropoff,
        "service_type": service_type,
        "confirm": confirm,
    }


@tool("ride_status", args_schema=RideStatusToolInput, description="Inspect current ride status and passenger/driver trip context.")
def ride_status_langchain_tool(trip_id: str | None = None) -> dict:
    """Return a ride status request envelope."""
    return {"tool_name": "ride_status", "trip_id": trip_id}


ride_booking_tool = register_tool(
    ToolSpec(
        name="ride",
        group="ride",
        description="Prepare ride booking actions that require user confirmation.",
        args_schema=RideToolInput,
        langchain_tool=ride_langchain_tool,
    )
)

ride_status_tool = register_tool(
    ToolSpec(
        name="ride_status",
        group="ride",
        description="Inspect ride status and passenger/driver trip context.",
        args_schema=RideStatusToolInput,
        langchain_tool=ride_status_langchain_tool,
    )
)
