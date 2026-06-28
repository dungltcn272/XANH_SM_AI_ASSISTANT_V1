from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool


class ExecutiveToolInput(BaseModel):
    query: str | None = None
    region: str | None = None
    horizon_days: int | None = Field(default=None, ge=1, le=365)


def _executive_envelope(tool_name: str, query: str | None = None, region: str | None = None, horizon_days: int | None = None) -> dict:
    return {"tool_name": tool_name, "query": query, "region": region, "horizon_days": horizon_days}


@tool("bi_analysis", args_schema=ExecutiveToolInput, description="Analyze strategic BI questions.")
def bi_analysis_langchain_tool(query: str | None = None, region: str | None = None, horizon_days: int | None = None) -> dict:
    """Return a BI analysis request envelope."""
    return _executive_envelope("bi_analysis", query, region, horizon_days)


@tool("forecast_simulation", args_schema=ExecutiveToolInput, description="Run forecast and voucher simulations.")
def forecast_simulation_langchain_tool(query: str | None = None, region: str | None = None, horizon_days: int | None = None) -> dict:
    """Return a forecast simulation request envelope."""
    return _executive_envelope("forecast_simulation", query, region, horizon_days)


@tool("churn_prediction", args_schema=ExecutiveToolInput, description="Estimate churn risk by customer segment.")
def churn_prediction_langchain_tool(query: str | None = None, region: str | None = None, horizon_days: int | None = None) -> dict:
    """Return a churn prediction request envelope."""
    return _executive_envelope("churn_prediction", query, region, horizon_days)


@tool("expansion_advisor", args_schema=ExecutiveToolInput, description="Advise expansion by region and product.")
def expansion_advisor_langchain_tool(query: str | None = None, region: str | None = None, horizon_days: int | None = None) -> dict:
    """Return an expansion advisor request envelope."""
    return _executive_envelope("expansion_advisor", query, region, horizon_days)


bi_analysis_tool = register_tool(ToolSpec(name="bi_analysis", group="executive", description="Analyze strategic BI questions.", args_schema=ExecutiveToolInput, langchain_tool=bi_analysis_langchain_tool))
forecast_simulation_tool = register_tool(ToolSpec(name="forecast_simulation", group="executive", description="Run forecast and voucher simulations.", args_schema=ExecutiveToolInput, langchain_tool=forecast_simulation_langchain_tool))
churn_prediction_tool = register_tool(ToolSpec(name="churn_prediction", group="executive", description="Estimate churn risk by customer segment.", args_schema=ExecutiveToolInput, langchain_tool=churn_prediction_langchain_tool))
expansion_advisor_tool = register_tool(ToolSpec(name="expansion_advisor", group="executive", description="Advise expansion by region and product.", args_schema=ExecutiveToolInput, langchain_tool=expansion_advisor_langchain_tool))
