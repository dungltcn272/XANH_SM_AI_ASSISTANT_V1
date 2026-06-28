from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    display_query: str | None = None
    conversation_id: str | None = None
    image_base64: str | None = None
    deep_search: bool = False
    persona: str = "customer"
    lat: float | None = None
    lng: float | None = None
    address: str | None = None
    budget_vnd: int | None = Field(default=None, ge=0)


class ChatMetadata(BaseModel):
    conversation_id: str
    run_id: str
    persona: str


class ChatMessageResponse(BaseModel):
    message_id: str | None = None
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
