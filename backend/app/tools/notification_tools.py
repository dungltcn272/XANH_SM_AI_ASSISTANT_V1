from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool


class NotificationToolInput(BaseModel):
    title: str = Field(..., description="Tiêu đề thông báo.")
    body: str = Field(..., description="Nội dung thông báo.")
    audience: str = Field(default="internal", description="Nhóm nhận thông báo.")


@tool("notification_send", args_schema=NotificationToolInput, description="Prepare notification actions for permitted internal users.")
def notification_send_langchain_tool(title: str, body: str, audience: str = "internal") -> dict:
    """Return a notification request envelope."""
    return {"tool_name": "notification_send", "title": title, "body": body, "audience": audience}


notification_tool = register_tool(
    ToolSpec(
        name="notification_send",
        group="notification",
        description="Prepare notification actions for permitted internal users.",
        args_schema=NotificationToolInput,
        langchain_tool=notification_send_langchain_tool,
    )
)
