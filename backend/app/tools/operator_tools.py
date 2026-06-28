from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool


class OperatorToolInput(BaseModel):
    query: str | None = None
    region: str | None = Field(default=None, description="Khu vực vận hành.")
    severity: str | None = Field(default=None, description="Mức độ ưu tiên nếu có.")


def _operator_envelope(tool_name: str, query: str | None = None, region: str | None = None, severity: str | None = None) -> dict:
    return {"tool_name": tool_name, "query": query, "region": region, "severity": severity}


@tool("fleet_monitor", args_schema=OperatorToolInput, description="Inspect online drivers and fleet status.")
def fleet_monitor_langchain_tool(query: str | None = None, region: str | None = None, severity: str | None = None) -> dict:
    """Return a fleet monitor request envelope."""
    return _operator_envelope("fleet_monitor", query, region, severity)


@tool("revenue_diagnostics", args_schema=OperatorToolInput, description="Explain operational revenue changes.")
def revenue_diagnostics_langchain_tool(query: str | None = None, region: str | None = None, severity: str | None = None) -> dict:
    """Return a revenue diagnostics request envelope."""
    return _operator_envelope("revenue_diagnostics", query, region, severity)


@tool("fraud_detection", args_schema=OperatorToolInput, description="Detect suspicious accounts or trips.")
def fraud_detection_langchain_tool(query: str | None = None, region: str | None = None, severity: str | None = None) -> dict:
    """Return a fraud detection request envelope."""
    return _operator_envelope("fraud_detection", query, region, severity)


@tool("incident_monitor", args_schema=OperatorToolInput, description="Monitor operational incidents.")
def incident_monitor_langchain_tool(query: str | None = None, region: str | None = None, severity: str | None = None) -> dict:
    """Return an incident monitor request envelope."""
    return _operator_envelope("incident_monitor", query, region, severity)


fleet_monitor_tool = register_tool(ToolSpec(name="fleet_monitor", group="operator", description="Inspect online drivers and fleet status.", args_schema=OperatorToolInput, langchain_tool=fleet_monitor_langchain_tool))
revenue_diagnostics_tool = register_tool(ToolSpec(name="revenue_diagnostics", group="operator", description="Explain operational revenue changes.", args_schema=OperatorToolInput, langchain_tool=revenue_diagnostics_langchain_tool))
fraud_detection_tool = register_tool(ToolSpec(name="fraud_detection", group="operator", description="Detect suspicious accounts or trips.", args_schema=OperatorToolInput, langchain_tool=fraud_detection_langchain_tool))
incident_monitor_tool = register_tool(ToolSpec(name="incident_monitor", group="operator", description="Monitor operational incidents.", args_schema=OperatorToolInput, langchain_tool=incident_monitor_langchain_tool))
