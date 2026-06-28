from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool

food_recommendation_tool = register_tool(
    ToolSpec(
        name="food",
        group="food",
        description="Recommend food and merchants from catalog, context, and preferences.",
    )
)
