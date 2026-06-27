from __future__ import annotations

from .common import *

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: generate_id("conv"))
    actor_id = Column(String, ForeignKey("actors.id"), nullable=True, index=True)
    persona_id = Column(String, ForeignKey("personas.id"), default="customer", nullable=False, index=True)
    title = Column(String, nullable=True)
    channel = Column(String, default="web", nullable=False)
    status = Column(String, default="active", nullable=False)
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

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: generate_id("msg"))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String, default="text", nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

    @property
    def pipeline_trace(self) -> str | None:
        return self.metadata_json

    @pipeline_trace.setter
    def pipeline_trace(self, value: str | None) -> None:
        self.metadata_json = value
