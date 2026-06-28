from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool

rag_tool = register_tool(
    ToolSpec(
        name="rag",
        group="rag",
        description="Search curated knowledge sources and answer with citations.",
    )
)

rag_driver_tool = register_tool(
    ToolSpec(
        name="rag_driver",
        group="rag",
        description="Search driver-facing operational knowledge.",
    )
)
