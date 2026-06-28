from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool


class PaymentToolInput(BaseModel):
    query: str | None = None
    amount_vnd: int | None = Field(default=None, ge=0)
    purpose: str | None = None


@tool("payment_stub", args_schema=PaymentToolInput, description="Prepare payment flows that require explicit confirmation.")
def payment_stub_langchain_tool(query: str | None = None, amount_vnd: int | None = None, purpose: str | None = None) -> dict:
    """Return a payment request envelope."""
    return {"tool_name": "payment_stub", "query": query, "amount_vnd": amount_vnd, "purpose": purpose}


payment_stub_tool = register_tool(
    ToolSpec(
        name="payment_stub",
        group="payment",
        description="Prepare payment flows that require explicit confirmation.",
        args_schema=PaymentToolInput,
        langchain_tool=payment_stub_langchain_tool,
    )
)
