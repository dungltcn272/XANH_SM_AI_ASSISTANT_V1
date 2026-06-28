from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool

demand_heatmap_tool = register_tool(
    ToolSpec(
        name="demand_heatmap",
        group="driver",
        description="Estimate driver hot zones and demand heatmap.",
    )
)

charging_tool = register_tool(
    ToolSpec(
        name="charging",
        group="driver",
        description="Find charging station options and battery-aware suggestions.",
    )
)
