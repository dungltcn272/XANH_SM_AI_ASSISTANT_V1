from __future__ import annotations

from .common import *

class Memory(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True, default=lambda: generate_id("mem"))
    actor_id = Column(String, ForeignKey("actors.id"), nullable=True, index=True)
    persona_id = Column(String, ForeignKey("personas.id"), nullable=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True, index=True)
    memory_type = Column(String, nullable=False, index=True)
    scope = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String, default="nlu", nullable=False)
    metadata_json = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    status = Column(String, default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time, index=True)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time, index=True)

    @property
    def user_id(self) -> str | None:
        return self.actor_id

    @user_id.setter
    def user_id(self, value: str | None) -> None:
        self.actor_id = value

    @property
    def guest_id(self) -> str | None:
        return self.actor_id

    @guest_id.setter
    def guest_id(self, value: str | None) -> None:
        self.actor_id = value

    @property
    def memory_metadata_json(self) -> str | None:
        return self.metadata_json

    @memory_metadata_json.setter
    def memory_metadata_json(self, value: str | None) -> None:
        self.metadata_json = value

class ProfileSnapshot(Base):
    __tablename__ = "profile_snapshots"

    id = Column(String, primary_key=True, default=lambda: generate_id("profile"))
    actor_id = Column(String, ForeignKey("actors.id"), nullable=False, index=True)
    persona_id = Column(String, ForeignKey("personas.id"), nullable=True, index=True)
    profile_json = Column(Text, nullable=False)
    source_memory_ids_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)

    @property
    def user_id(self) -> str | None:
        return self.actor_id

    @user_id.setter
    def user_id(self, value: str | None) -> None:
        self.actor_id = value

    @property
    def guest_id(self) -> str | None:
        return self.actor_id

    @guest_id.setter
    def guest_id(self, value: str | None) -> None:
        self.actor_id = value

    def _get_profile_value(self, key: str, default: str | None = None) -> str | None:
        import json

        try:
            payload = json.loads(self.profile_json or "{}")
        except (TypeError, json.JSONDecodeError):
            payload = {}
        return payload.get(key, default)

    def _set_profile_value(self, key: str, value: str | None) -> None:
        import json

        try:
            payload = json.loads(self.profile_json or "{}")
        except (TypeError, json.JSONDecodeError):
            payload = {}
        payload[key] = value
        self.profile_json = json.dumps(payload, ensure_ascii=False)

    @property
    def current_location_json(self) -> str | None:
        return self._get_profile_value("current_location_json")

    @current_location_json.setter
    def current_location_json(self, value: str | None) -> None:
        self._set_profile_value("current_location_json", value)

    @property
    def saved_places_json(self) -> str | None:
        return self._get_profile_value("saved_places_json", "[]")

    @saved_places_json.setter
    def saved_places_json(self, value: str | None) -> None:
        self._set_profile_value("saved_places_json", value)

    @property
    def liked_items_json(self) -> str | None:
        return self._get_profile_value("liked_items_json", "[]")

    @liked_items_json.setter
    def liked_items_json(self, value: str | None) -> None:
        self._set_profile_value("liked_items_json", value)

    @property
    def disliked_items_json(self) -> str | None:
        return self._get_profile_value("disliked_items_json", "[]")

    @disliked_items_json.setter
    def disliked_items_json(self, value: str | None) -> None:
        self._set_profile_value("disliked_items_json", value)

    @property
    def preferred_categories_json(self) -> str | None:
        return self._get_profile_value("preferred_categories_json")

    @property
    def preferred_tags_json(self) -> str | None:
        return self._get_profile_value("preferred_tags_json")

    @property
    def avoided_tags_json(self) -> str | None:
        return self._get_profile_value("avoided_tags_json")

    @property
    def budget_profile_json(self) -> str | None:
        return self._get_profile_value("budget_profile_json")

    @property
    def allergies_json(self) -> str | None:
        return self._get_profile_value("allergies_json")

    @property
    def profile_stats_json(self) -> str | None:
        return self._get_profile_value("profile_stats_json")

class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"

    id = Column(String, primary_key=True, default=lambda: generate_id("summary"))
    conversation_id = Column(String, ForeignKey("conversations.id"), unique=True, nullable=False, index=True)
    summary_json = Column(Text, nullable=False)
    last_message_id = Column(String, ForeignKey("messages.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)
