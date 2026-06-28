from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool

map_lookup_tool = register_tool(
    ToolSpec(
        name="map",
        group="map",
        description="Resolve map, distance, ETA, and Leaflet-friendly location payloads.",
    )
)
