from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


ToolHandler = Callable[..., Any]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    group: str
    description: str
    args_schema: type[BaseModel] | None = None
    handler: ToolHandler | None = None
    langchain_tool: Any | None = None

    @property
    def lc_tool(self) -> Any | None:
        return self.langchain_tool
