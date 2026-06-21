from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_entity
from app.db.database import get_db
from app.db.models import UserAssistantSetting
from app.prompts.system_prompts import ASSISTANT_PERSONAS, DEFAULT_ASSISTANT_PERSONA


router = APIRouter()


class AssistantPreferenceRequest(BaseModel):
    assistant_persona: str


def _normalize_persona(value: str | None) -> str:
    persona = (value or DEFAULT_ASSISTANT_PERSONA).strip().lower()
    if persona not in ASSISTANT_PERSONAS:
        raise HTTPException(status_code=400, detail="Unsupported assistant persona")
    return persona


@router.get("")
def get_preferences(
    db: Session = Depends(get_db),
    entity: dict = Depends(get_current_entity),
):
    if entity.get("type") != "user" or not entity.get("entity"):
        return {"assistant_persona": DEFAULT_ASSISTANT_PERSONA, "available_personas": ASSISTANT_PERSONAS}
    user = entity["entity"]
    setting = db.query(UserAssistantSetting).filter(UserAssistantSetting.user_id == user.id).first()
    return {
        "assistant_persona": setting.assistant_persona if setting else DEFAULT_ASSISTANT_PERSONA,
        "available_personas": ASSISTANT_PERSONAS,
    }


@router.put("")
def update_preferences(
    req: AssistantPreferenceRequest,
    db: Session = Depends(get_db),
    entity: dict = Depends(get_current_entity),
):
    if entity.get("type") != "user" or not entity.get("entity"):
        raise HTTPException(status_code=401, detail="Login required")
    user = entity["entity"]
    persona = _normalize_persona(req.assistant_persona)
    setting = db.query(UserAssistantSetting).filter(UserAssistantSetting.user_id == user.id).first()
    if not setting:
        setting = UserAssistantSetting(user_id=user.id, assistant_persona=persona)
        db.add(setting)
    else:
        setting.assistant_persona = persona
    db.commit()
    return {"assistant_persona": persona, "available_personas": ASSISTANT_PERSONAS}
