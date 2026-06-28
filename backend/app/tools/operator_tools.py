from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool

fleet_monitor_tool = register_tool(
    ToolSpec(name="fleet_monitor", group="operator", description="Inspect online drivers and fleet status.")
)
revenue_diagnostics_tool = register_tool(
    ToolSpec(name="revenue_diagnostics", group="operator", description="Explain operational revenue changes.")
)
fraud_detection_tool = register_tool(
    ToolSpec(name="fraud_detection", group="operator", description="Detect suspicious accounts or trips.")
)
incident_monitor_tool = register_tool(
    ToolSpec(name="incident_monitor", group="operator", description="Monitor operational incidents.")
)
