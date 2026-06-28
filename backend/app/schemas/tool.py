from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCallRequest(BaseModel):
    tool_name: str
    persona: str = "customer"
    input: dict[str, Any] = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    tool_name: str
    tool_group: str
    permission_status: str
    output: dict[str, Any] = Field(default_factory=dict)
