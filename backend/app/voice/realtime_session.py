from __future__ import annotations

import uuid


def create_realtime_voice_session(persona: str, language: str = "vi-VN") -> dict:
    return {"session_id": f"voice_{uuid.uuid4().hex}", "persona": persona, "language": language}
