from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool

payment_stub_tool = register_tool(
    ToolSpec(
        name="payment_stub",
        group="payment",
        description="Prepare payment flows that require explicit confirmation.",
    )
)
