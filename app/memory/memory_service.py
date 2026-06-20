from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import ConversationSummary, Message, UserMemory, UserProfile


VALID_MEMORY_SCOPES = {"general", "food", "rag", "project", "support"}
VALID_MEMORY_TYPES = {"fact", "preference", "dislike", "goal", "constraint", "location", "behavior"}


def _json_or_default(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _identity(user_id: str | None = None, guest_id: str | None = None) -> dict[str, str | None]:
    return {
        "user_id": user_id if user_id and user_id != "anonymous" else None,
        "guest_id": guest_id if guest_id and guest_id != "anonymous" else None,
    }


def _normalize_text(value: str | None) -> str:
    normalized = unicodedata.normalize("NFD", value or "")
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    text = without_marks.replace("đ", "d").replace("Đ", "D")
    return re.sub(r"\s+", " ", text.casefold()).strip()


def _query_terms(query: str, limit: int = 8) -> list[str]:
    stop_words = {
        "anh", "chị", "em", "tôi", "mình", "của", "cho", "với", "và", "là",
        "có", "không", "gì", "nào", "về", "ở", "đâu", "như", "thế", "này",
    }
    terms = []
    for term in re.findall(r"[\wÀ-ỹ]+", _normalize_text(query)):
        if len(term) < 3 or term in stop_words:
            continue
        terms.append(term)
    return list(dict.fromkeys(terms))[:limit]


class MemoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_recent_messages(self, conversation_id: str, limit: int = 12) -> list[Message]:
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(messages))

    def save_message(self, conversation_id: str, role: str, content: str) -> Message:
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_or_create_user_profile(
        self,
        user_id: str | None = None,
        guest_id: str | None = None,
    ) -> UserProfile | None:
        ident = _identity(user_id, guest_id)
        if not ident["user_id"] and not ident["guest_id"]:
            return None

        query = self.db.query(UserProfile)
        if ident["user_id"]:
            row = query.filter(UserProfile.user_id == ident["user_id"]).first()
        else:
            row = query.filter(UserProfile.guest_id == ident["guest_id"]).first()
        if row:
            return row

        row = UserProfile(user_id=ident["user_id"], guest_id=ident["guest_id"])
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_profile_payload(
        self,
        user_id: str | None = None,
        guest_id: str | None = None,
    ) -> dict[str, Any]:
        profile = self.get_or_create_user_profile(user_id=user_id, guest_id=guest_id)
        if not profile:
            return {}
        return {
            "profile_cache_note": "Derived from active user_memories; user_memories remain the source of truth.",
            "display_name": profile.display_name,
            "facts": _json_or_default(profile.facts_json, []),
            "preferences": _json_or_default(profile.preferences_json, []),
            "goals": _json_or_default(profile.goals_json, []),
            "constraints": _json_or_default(profile.constraints_json, []),
            "behaviors": _json_or_default(getattr(profile, "behaviors_json", None), []),
            "profile_stats": _json_or_default(profile.profile_stats_json, {}),
        }

    def get_conversation_summary(self, conversation_id: str | None) -> dict[str, Any]:
        if not conversation_id:
            return {}
        row = (
            self.db.query(ConversationSummary)
            .filter(ConversationSummary.conversation_id == conversation_id)
            .first()
        )
        if not row:
            return {}
        return _json_or_default(row.summary_json, {})

    def get_long_term_memory(
        self,
        user_id: str | None = None,
        guest_id: str | None = None,
        query: str = "",
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        ident = _identity(user_id, guest_id)
        if not ident["user_id"] and not ident["guest_id"]:
            return []

        db_query = self.db.query(UserMemory).filter(UserMemory.status == "active")
        if ident["user_id"]:
            db_query = db_query.filter(UserMemory.user_id == ident["user_id"])
        else:
            db_query = db_query.filter(UserMemory.guest_id == ident["guest_id"])

        terms = _query_terms(query)
        if terms:
            like_filters = [UserMemory.content.ilike(f"%{term}%") for term in terms]
            matched = db_query.filter(or_(*like_filters)).order_by(UserMemory.updated_at.desc()).limit(limit).all()
            if len(matched) >= limit:
                return [self._memory_payload(row) for row in matched]
            seen_ids = {row.id for row in matched}
            fallback = (
                db_query.filter(~UserMemory.id.in_(seen_ids)) if seen_ids else db_query
            ).order_by(UserMemory.updated_at.desc()).limit(limit - len(matched)).all()
            return [self._memory_payload(row) for row in [*matched, *fallback]]

        rows = db_query.order_by(UserMemory.updated_at.desc()).limit(limit).all()
        return [self._memory_payload(row) for row in rows]

    def build_assistant_context(
        self,
        *,
        user_id: str | None = None,
        guest_id: str | None = None,
        conversation_id: str | None = None,
        query: str = "",
    ) -> dict[str, Any]:
        return {
            "profile": self.get_profile_payload(user_id=user_id, guest_id=guest_id),
            "relevant_memories": self.get_long_term_memory(
                user_id=user_id,
                guest_id=guest_id,
                query=query,
            ),
            "conversation_summary": self.get_conversation_summary(conversation_id),
        }

    def save_memory_candidates(
        self,
        *,
        candidates: list[dict[str, Any]] | None,
        user_id: str | None = None,
        guest_id: str | None = None,
        conversation_id: str | None = None,
        message_id: str | None = None,
        source: str = "nlu",
    ) -> list[UserMemory]:
        ident = _identity(user_id, guest_id)
        if not candidates or (not ident["user_id"] and not ident["guest_id"]):
            return []

        saved: list[UserMemory] = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = _normalize_text(candidate.get("content"))
            if len(content) < 8:
                continue

            scope = candidate.get("scope") or "general"
            memory_type = candidate.get("memory_type") or candidate.get("type") or "fact"
            if scope not in VALID_MEMORY_SCOPES:
                scope = "general"
            if memory_type not in VALID_MEMORY_TYPES:
                memory_type = "fact"

            confidence = self._safe_confidence(candidate.get("confidence"))
            if confidence < 0.55:
                continue

            existing = self._find_existing_memory(content, ident["user_id"], ident["guest_id"])
            if existing:
                existing.scope = scope
                existing.memory_type = memory_type
                existing.confidence = max(float(existing.confidence or 0), confidence)
                existing.message_id = message_id or existing.message_id
                existing.conversation_id = conversation_id or existing.conversation_id
                existing.source = source
                existing.memory_metadata_json = _dump_json(candidate.get("metadata") or {})
                saved.append(existing)
            else:
                row = UserMemory(
                    user_id=ident["user_id"],
                    guest_id=ident["guest_id"],
                    conversation_id=conversation_id,
                    message_id=message_id,
                    scope=scope,
                    memory_type=memory_type,
                    content=candidate.get("content", "").strip(),
                    confidence=confidence,
                    source=source,
                    memory_metadata_json=_dump_json(candidate.get("metadata") or {}),
                )
                self.db.add(row)
                saved.append(row)

        if saved:
            self.db.commit()
            for row in saved:
                self.db.refresh(row)
            self._refresh_profile_from_memories(ident["user_id"], ident["guest_id"])
            self._sync_location_candidates_to_food_profile(candidates, ident["user_id"], ident["guest_id"])
        return saved

    def extract_and_save_facts(
        self,
        user_id: str | None,
        content: str,
        *,
        guest_id: str | None = None,
        conversation_id: str | None = None,
        message_id: str | None = None,
        candidates: list[dict[str, Any]] | None = None,
    ) -> list[UserMemory]:
        # The extractor lives in NLU. This method is the write-side boundary.
        return self.save_memory_candidates(
            candidates=candidates,
            user_id=user_id,
            guest_id=guest_id,
            conversation_id=conversation_id,
            message_id=message_id,
            source="nlu",
        )

    def _memory_payload(self, row: UserMemory) -> dict[str, Any]:
        return {
            "id": row.id,
            "scope": row.scope,
            "memory_type": row.memory_type,
            "content": row.content,
            "confidence": row.confidence,
            "source": row.source,
            "metadata": _json_or_default(row.memory_metadata_json, {}),
        }

    def _find_existing_memory(
        self,
        normalized_content: str,
        user_id: str | None,
        guest_id: str | None,
    ) -> UserMemory | None:
        query = self.db.query(UserMemory).filter(UserMemory.status == "active")
        if user_id:
            query = query.filter(UserMemory.user_id == user_id)
        else:
            query = query.filter(UserMemory.guest_id == guest_id)
        for row in query.order_by(UserMemory.updated_at.desc()).limit(120).all():
            if _normalize_text(row.content) == normalized_content:
                return row
        return None

    def _refresh_profile_from_memories(self, user_id: str | None, guest_id: str | None) -> None:
        profile = self.get_or_create_user_profile(user_id=user_id, guest_id=guest_id)
        if not profile:
            return

        memories = self.get_long_term_memory(user_id=user_id, guest_id=guest_id, limit=80)
        grouped = {
            "facts": [],
            "preferences": [],
            "goals": [],
            "constraints": [],
            "behaviors": [],
        }
        display_name = profile.display_name
        for memory in memories:
            item = {
                "content": memory["content"],
                "scope": memory["scope"],
                "confidence": memory["confidence"],
            }
            metadata = memory.get("metadata") or {}
            if metadata:
                item["metadata"] = metadata
            memory_type = memory["memory_type"]
            if memory_type == "goal":
                grouped["goals"].append(item)
            elif memory_type in {"constraint", "dislike", "location"}:
                grouped["constraints"].append(item)
            elif memory_type == "behavior":
                grouped["behaviors"].append(item)
            elif memory_type == "preference":
                grouped["preferences"].append(item)
            else:
                grouped["facts"].append(item)
            if not display_name:
                display_name = self._display_name_from_memory(memory)

        profile.display_name = display_name
        profile.facts_json = _dump_json(grouped["facts"][:24])
        profile.preferences_json = _dump_json(grouped["preferences"][:24])
        profile.goals_json = _dump_json(grouped["goals"][:12])
        profile.constraints_json = _dump_json(grouped["constraints"][:24])
        if hasattr(profile, "behaviors_json"):
            profile.behaviors_json = _dump_json(grouped["behaviors"][:24])
        profile.profile_stats_json = _dump_json({
            "memory_count": len(memories),
            "profile_source": "derived_from_user_memories",
        })
        self.db.commit()

    @staticmethod
    def _display_name_from_memory(memory: dict[str, Any]) -> str | None:
        metadata = memory.get("metadata") or {}
        for key in ("display_name", "name", "user_name"):
            value = metadata.get(key)
            if isinstance(value, str) and 1 <= len(value.strip()) <= 80:
                return value.strip()
        content = memory.get("content") or ""
        patterns = [
            r"(?:tên tôi là|tôi tên là|mình tên là|gọi tôi là)\s+([^,.!?\n]{1,80})",
            r"(?:anh/chị tên là)\s+([^,.!?\n]{1,80})",
        ]
        lowered = content.casefold()
        for pattern in patterns:
            match = re.search(pattern, lowered, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip().title()
        return None

    def _sync_location_candidates_to_food_profile(
        self,
        candidates: list[dict[str, Any]] | None,
        user_id: str | None,
        guest_id: str | None,
    ) -> None:
        if not candidates:
            return
        try:
            from app.food_recommendation.profile_store import save_food_location

            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                if candidate.get("memory_type") != "location" and candidate.get("type") != "location":
                    continue
                metadata = candidate.get("metadata") or {}
                lat = metadata.get("lat") or metadata.get("latitude")
                lng = metadata.get("lng") or metadata.get("lon") or metadata.get("longitude")
                if lat is None or lng is None:
                    continue
                label = metadata.get("label") or metadata.get("name") or metadata.get("type") or "Vị trí đã lưu"
                save_food_location(
                    self.db,
                    user_id=user_id,
                    guest_id=guest_id,
                    location={
                        "id": metadata.get("id") or metadata.get("type") or label,
                        "type": metadata.get("type") or metadata.get("id"),
                        "label": label,
                        "address": metadata.get("address") or candidate.get("content"),
                        "lat": lat,
                        "lng": lng,
                        "source": "nlu_memory",
                    },
                    set_current=bool(metadata.get("set_current", True)),
                )
        except Exception:
            return

    @staticmethod
    def _safe_confidence(value: Any) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.7
