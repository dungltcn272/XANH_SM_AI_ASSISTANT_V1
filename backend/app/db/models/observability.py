from __future__ import annotations

from .common import *

class AssistantRun(Base):
    __tablename__ = "assistant_runs"

    id = Column(String, primary_key=True, default=lambda: generate_id("run"))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True)
    actor_id = Column(String, ForeignKey("actors.id"), nullable=True, index=True)
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    intent = Column(String, nullable=True, index=True)
    status = Column(String, default="running", nullable=False)
    model_name = Column(String, nullable=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    finished_at = Column(DateTime(timezone=True), nullable=True)

class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(String, primary_key=True, default=lambda: generate_id("toolcall"))
    run_id = Column(String, ForeignKey("assistant_runs.id"), nullable=False, index=True)
    tool_name = Column(String, nullable=False, index=True)
    tool_group = Column(String, nullable=False, index=True)
    permission_status = Column(String, nullable=False)
    input_json = Column(Text, nullable=True)
    output_json = Column(Text, nullable=True)
    error_json = Column(Text, nullable=True)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class AiTraceEvent(Base):
    __tablename__ = "ai_trace_events"

    id = Column(String, primary_key=True, default=lambda: generate_id("trace"))
    run_id = Column(String, ForeignKey("assistant_runs.id"), nullable=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)
    persona_id = Column(String, nullable=True, index=True)
    node = Column(String, nullable=False, index=True)
    event = Column(String, nullable=False, index=True)
    level = Column(String, default="INFO", nullable=False, index=True)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time, index=True)

    @property
    def query(self) -> str | None:
        return None

    @property
    def intent(self) -> str | None:
        return None
