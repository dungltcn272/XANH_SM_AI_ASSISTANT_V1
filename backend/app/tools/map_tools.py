from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool


class MapToolInput(BaseModel):
    origin: str | None = Field(default=None, description="Điểm bắt đầu.")
    destination: str | None = Field(default=None, description="Điểm kết thúc.")
    lat: float | None = None
    lng: float | None = None


@tool("map", args_schema=MapToolInput, description="Resolve map, distance, ETA, and Leaflet-friendly location payloads.")
def map_langchain_tool(origin: str | None = None, destination: str | None = None, lat: float | None = None, lng: float | None = None) -> dict:
    """Return a map request envelope."""
    return {"tool_name": "map", "origin": origin, "destination": destination, "lat": lat, "lng": lng}


map_lookup_tool = register_tool(
    ToolSpec(
        name="map",
        group="map",
        description="Resolve map, distance, ETA, and Leaflet-friendly location payloads.",
        args_schema=MapToolInput,
        langchain_tool=map_langchain_tool,
    )
)
