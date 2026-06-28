from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool


class FoodRecommendationToolInput(BaseModel):
    query: str = Field(..., description="Nhu cầu ăn uống hoặc món/quán người dùng muốn tìm.")
    lat: float | None = Field(default=None, description="Vĩ độ vị trí tìm kiếm nếu có.")
    lng: float | None = Field(default=None, description="Kinh độ vị trí tìm kiếm nếu có.")
    address: str | None = Field(default=None, description="Địa chỉ tìm kiếm nếu chưa có lat/lng.")
    budget_vnd: int | None = Field(default=None, ge=0, description="Ngân sách tối đa bằng VND.")
    limit: int = Field(default=8, ge=1, le=20, description="Số món/quán trả về.")


@tool("food", args_schema=FoodRecommendationToolInput, description="Recommend food and merchants from catalog, location, preferences, and budget.")
def food_langchain_tool(
    query: str,
    lat: float | None = None,
    lng: float | None = None,
    address: str | None = None,
    budget_vnd: int | None = None,
    limit: int = 8,
) -> dict:
    """Return a food recommendation request envelope for the orchestrator to execute with DB context."""
    return {
        "tool_name": "food",
        "query": query,
        "lat": lat,
        "lng": lng,
        "address": address,
        "budget_vnd": budget_vnd,
        "limit": limit,
    }


food_recommendation_tool = register_tool(
    ToolSpec(
        name="food",
        group="food",
        description="Recommend food and merchants from catalog, context, and preferences.",
        args_schema=FoodRecommendationToolInput,
        langchain_tool=food_langchain_tool,
    )
)
