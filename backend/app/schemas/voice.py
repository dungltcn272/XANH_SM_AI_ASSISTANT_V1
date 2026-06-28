from __future__ import annotations

from pydantic import BaseModel


class VoiceSessionRequest(BaseModel):
    persona: str = "customer"
    language: str = "vi-VN"


class VoiceSessionResponse(BaseModel):
    session_id: str
    persona: str
    language: str
    status: str = "created"
