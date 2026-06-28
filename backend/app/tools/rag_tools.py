from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool


class RagToolInput(BaseModel):
    query: str = Field(..., description="Câu hỏi cần truy xuất trong kho tri thức Xanh SM.")
    top_k: int | None = Field(default=None, ge=1, le=50, description="Số lượng ứng viên retrieval tối đa.")


@tool("rag", args_schema=RagToolInput, description="Search curated Xanh SM knowledge and answer with grounded citations.")
def rag_langchain_tool(query: str, top_k: int | None = None) -> dict:
    """Return a RAG tool request envelope for the orchestrator to execute with DB context."""
    return {"tool_name": "rag", "query": query, "top_k": top_k}


@tool("rag_driver", args_schema=RagToolInput, description="Search driver-facing Xanh SM operational knowledge.")
def rag_driver_langchain_tool(query: str, top_k: int | None = None) -> dict:
    """Return a driver RAG tool request envelope for the orchestrator to execute with DB context."""
    return {"tool_name": "rag_driver", "query": query, "top_k": top_k}


rag_tool = register_tool(
    ToolSpec(
        name="rag",
        group="rag",
        description="Search curated knowledge sources and answer with citations.",
        args_schema=RagToolInput,
        langchain_tool=rag_langchain_tool,
    )
)

rag_driver_tool = register_tool(
    ToolSpec(
        name="rag_driver",
        group="rag",
        description="Search driver-facing operational knowledge.",
        args_schema=RagToolInput,
        langchain_tool=rag_driver_langchain_tool,
    )
)
