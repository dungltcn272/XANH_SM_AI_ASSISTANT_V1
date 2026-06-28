import uuid

from fastapi import APIRouter

from app.schemas.voice import VoiceSessionRequest, VoiceSessionResponse


router = APIRouter()


@router.post("/session", response_model=VoiceSessionResponse)
def create_voice_session(req: VoiceSessionRequest) -> VoiceSessionResponse:
    return VoiceSessionResponse(session_id=f"voice_{uuid.uuid4().hex}", persona=req.persona, language=req.language)
