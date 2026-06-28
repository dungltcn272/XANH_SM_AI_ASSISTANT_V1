from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool

travel_planning_tool = register_tool(
    ToolSpec(
        name="travel",
        group="travel",
        description="Plan VinPearl, VinWonders, hotel, and itinerary experiences.",
    )
)

commerce_tool = register_tool(
    ToolSpec(
        name="commerce",
        group="commerce",
        description="Recommend Vin ecosystem commerce, voucher, and upsell options.",
    )
)
