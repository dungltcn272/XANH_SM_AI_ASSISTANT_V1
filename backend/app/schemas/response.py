from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str


class PersonaResponse(BaseModel):
    id: str
    display_name: str
    prompt_key: str
    allowed_tools: list[str] = Field(default_factory=list)
    memory_scopes: list[str] = Field(default_factory=list)
    data_scopes: list[str] = Field(default_factory=list)
    requires_auth: bool = False


class CapabilityResponse(BaseModel):
    persona: str
    tools: list[str]
    demo_queries: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
