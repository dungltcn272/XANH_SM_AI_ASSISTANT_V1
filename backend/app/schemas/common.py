from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ApiEnvelope(BaseModel):
    ok: bool = True
    data: Any | None = None
    error: ErrorBody | None = None


class Timestamped(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
