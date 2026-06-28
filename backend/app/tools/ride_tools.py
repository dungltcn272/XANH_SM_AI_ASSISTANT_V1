from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool

ride_booking_tool = register_tool(
    ToolSpec(
        name="ride",
        group="ride",
        description="Prepare ride booking actions that require user confirmation.",
    )
)

ride_status_tool = register_tool(
    ToolSpec(
        name="ride_status",
        group="ride",
        description="Inspect ride status and passenger/driver trip context.",
    )
)
