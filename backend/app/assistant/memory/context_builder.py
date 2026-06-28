from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.assistant.memory.long_term_memory import get_scoped_memories
from app.assistant.memory.user_profile_memory import get_profile_snapshot
from app.assistant.memory.working_memory import get_recent_turns
from app.assistant.personas import get_persona_config


@dataclass
class AssistantContext:
    recent_turns: list[dict[str, str]] = field(default_factory=list)
    memories: list[dict[str, object]] = field(default_factory=list)
    profile: dict = field(default_factory=dict)


def build_assistant_context(
    db: Session,
    *,
    actor_id: str | None,
    conversation_id: str | None,
    persona_id: str,
) -> AssistantContext:
    persona = get_persona_config(persona_id)
    return AssistantContext(
        recent_turns=get_recent_turns(db, conversation_id),
        memories=get_scoped_memories(db, actor_id=actor_id, persona_id=persona.persona_id.value, scopes=persona.memory_scopes),
        profile=get_profile_snapshot(db, actor_id=actor_id, persona_id=persona.persona_id.value),
    )
