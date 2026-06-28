from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool

merchant_analytics_tool = register_tool(
    ToolSpec(
        name="merchant_analytics",
        group="merchant",
        description="Analyze merchant revenue, menu performance, reviews, and promotions.",
    )
)

menu_analysis_tool = register_tool(
    ToolSpec(name="menu_analysis", group="merchant", description="Analyze menu item performance.")
)
review_analysis_tool = register_tool(
    ToolSpec(name="review_analysis", group="merchant", description="Summarize review sentiment and topics.")
)
promotion_advisor_tool = register_tool(
    ToolSpec(name="promotion_advisor", group="merchant", description="Suggest promotion timing and discount.")
)
menu_ocr_tool = register_tool(
    ToolSpec(name="menu_ocr", group="merchant", description="Extract and analyze menu images.")
)
