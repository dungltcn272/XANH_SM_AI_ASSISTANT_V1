from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool

notification_tool = register_tool(
    ToolSpec(
        name="notification_send",
        group="notification",
        description="Prepare notification actions for permitted internal users.",
    )
)
