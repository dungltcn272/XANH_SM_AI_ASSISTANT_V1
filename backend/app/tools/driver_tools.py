from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool


class DriverAreaToolInput(BaseModel):
    query: str | None = Field(default=None, description="Câu hỏi hoặc khu vực tài xế quan tâm.")
    lat: float | None = None
    lng: float | None = None
    radius_km: float | None = Field(default=None, ge=0)


@tool("demand_heatmap", args_schema=DriverAreaToolInput, description="Estimate driver hot zones and demand heatmap.")
def demand_heatmap_langchain_tool(query: str | None = None, lat: float | None = None, lng: float | None = None, radius_km: float | None = None) -> dict:
    """Return a demand heatmap request envelope."""
    return {"tool_name": "demand_heatmap", "query": query, "lat": lat, "lng": lng, "radius_km": radius_km}


@tool("charging", args_schema=DriverAreaToolInput, description="Find charging station options and battery-aware suggestions.")
def charging_langchain_tool(query: str | None = None, lat: float | None = None, lng: float | None = None, radius_km: float | None = None) -> dict:
    """Return a charging station request envelope."""
    return {"tool_name": "charging", "query": query, "lat": lat, "lng": lng, "radius_km": radius_km}


demand_heatmap_tool = register_tool(
    ToolSpec(
        name="demand_heatmap",
        group="driver",
        description="Estimate driver hot zones and demand heatmap.",
        args_schema=DriverAreaToolInput,
        langchain_tool=demand_heatmap_langchain_tool,
    )
)

charging_tool = register_tool(
    ToolSpec(
        name="charging",
        group="driver",
        description="Find charging station options and battery-aware suggestions.",
        args_schema=DriverAreaToolInput,
        langchain_tool=charging_langchain_tool,
    )
)
