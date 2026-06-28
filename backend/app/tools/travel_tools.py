from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool


class TravelToolInput(BaseModel):
    query: str = Field(..., description="Nhu cầu du lịch hoặc trải nghiệm Vin ecosystem.")
    location: str | None = None
    budget_vnd: int | None = Field(default=None, ge=0)


@tool("travel", args_schema=TravelToolInput, description="Plan VinPearl, VinWonders, hotel, and itinerary experiences.")
def travel_langchain_tool(query: str, location: str | None = None, budget_vnd: int | None = None) -> dict:
    """Return a travel planning request envelope."""
    return {"tool_name": "travel", "query": query, "location": location, "budget_vnd": budget_vnd}


@tool("commerce", args_schema=TravelToolInput, description="Recommend Vin ecosystem commerce, voucher, and upsell options.")
def commerce_langchain_tool(query: str, location: str | None = None, budget_vnd: int | None = None) -> dict:
    """Return a commerce recommendation request envelope."""
    return {"tool_name": "commerce", "query": query, "location": location, "budget_vnd": budget_vnd}


travel_planning_tool = register_tool(
    ToolSpec(
        name="travel",
        group="travel",
        description="Plan VinPearl, VinWonders, hotel, and itinerary experiences.",
        args_schema=TravelToolInput,
        langchain_tool=travel_langchain_tool,
    )
)

commerce_tool = register_tool(
    ToolSpec(
        name="commerce",
        group="commerce",
        description="Recommend Vin ecosystem commerce, voucher, and upsell options.",
        args_schema=TravelToolInput,
        langchain_tool=commerce_langchain_tool,
    )
)
