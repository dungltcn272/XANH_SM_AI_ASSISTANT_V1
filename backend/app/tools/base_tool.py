from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


ToolHandler = Callable[..., Any]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    group: str
    description: str
    handler: ToolHandler | None = None
