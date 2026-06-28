from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool


class MerchantToolInput(BaseModel):
    query: str | None = Field(default=None, description="Câu hỏi phân tích của merchant.")
    merchant_id: str | None = Field(default=None, description="Merchant id nếu đã xác định.")
    date_range: str | None = Field(default=None, description="Khoảng thời gian phân tích.")


def _merchant_envelope(tool_name: str, query: str | None = None, merchant_id: str | None = None, date_range: str | None = None) -> dict:
    return {"tool_name": tool_name, "query": query, "merchant_id": merchant_id, "date_range": date_range}


@tool("merchant_analytics", args_schema=MerchantToolInput, description="Analyze merchant revenue, menu performance, reviews, and promotions.")
def merchant_analytics_langchain_tool(query: str | None = None, merchant_id: str | None = None, date_range: str | None = None) -> dict:
    """Return a merchant analytics request envelope."""
    return _merchant_envelope("merchant_analytics", query, merchant_id, date_range)


@tool("menu_analysis", args_schema=MerchantToolInput, description="Analyze menu item performance.")
def menu_analysis_langchain_tool(query: str | None = None, merchant_id: str | None = None, date_range: str | None = None) -> dict:
    """Return a menu analysis request envelope."""
    return _merchant_envelope("menu_analysis", query, merchant_id, date_range)


@tool("review_analysis", args_schema=MerchantToolInput, description="Summarize review sentiment and topics.")
def review_analysis_langchain_tool(query: str | None = None, merchant_id: str | None = None, date_range: str | None = None) -> dict:
    """Return a review analysis request envelope."""
    return _merchant_envelope("review_analysis", query, merchant_id, date_range)


@tool("promotion_advisor", args_schema=MerchantToolInput, description="Suggest promotion timing and discount.")
def promotion_advisor_langchain_tool(query: str | None = None, merchant_id: str | None = None, date_range: str | None = None) -> dict:
    """Return a promotion advisor request envelope."""
    return _merchant_envelope("promotion_advisor", query, merchant_id, date_range)


@tool("menu_ocr", args_schema=MerchantToolInput, description="Extract and analyze menu images.")
def menu_ocr_langchain_tool(query: str | None = None, merchant_id: str | None = None, date_range: str | None = None) -> dict:
    """Return a menu OCR request envelope."""
    return _merchant_envelope("menu_ocr", query, merchant_id, date_range)


merchant_analytics_tool = register_tool(ToolSpec(name="merchant_analytics", group="merchant", description="Analyze merchant revenue, menu performance, reviews, and promotions.", args_schema=MerchantToolInput, langchain_tool=merchant_analytics_langchain_tool))
menu_analysis_tool = register_tool(ToolSpec(name="menu_analysis", group="merchant", description="Analyze menu item performance.", args_schema=MerchantToolInput, langchain_tool=menu_analysis_langchain_tool))
review_analysis_tool = register_tool(ToolSpec(name="review_analysis", group="merchant", description="Summarize review sentiment and topics.", args_schema=MerchantToolInput, langchain_tool=review_analysis_langchain_tool))
promotion_advisor_tool = register_tool(ToolSpec(name="promotion_advisor", group="merchant", description="Suggest promotion timing and discount.", args_schema=MerchantToolInput, langchain_tool=promotion_advisor_langchain_tool))
menu_ocr_tool = register_tool(ToolSpec(name="menu_ocr", group="merchant", description="Extract and analyze menu images.", args_schema=MerchantToolInput, langchain_tool=menu_ocr_langchain_tool))
