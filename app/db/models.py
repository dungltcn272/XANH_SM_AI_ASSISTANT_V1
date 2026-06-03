import enum
import uuid
from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Integer, Enum, Boolean
from sqlalchemy.sql import func
from app.db.database import Base

def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: generate_id("user"))
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GuestSession(Base):
    __tablename__ = "guest_sessions"
    id = Column(String, primary_key=True, default=lambda: generate_id("guest"))
    session_token = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=lambda: generate_id("conv"))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    guest_id = Column(String, ForeignKey("guest_sessions.id"), nullable=True)
    title = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: generate_id("msg"))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RagRequestLog(Base):
    __tablename__ = "rag_request_logs"
    id = Column(String, primary_key=True, default=lambda: generate_id("req"))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    original_query = Column(Text)
    rewritten_query = Column(Text, nullable=True)
    final_answer = Column(Text, nullable=True)
    intent = Column(String, nullable=True)
    
    # Telemetry
    search_latency_ms = Column(Float, default=0)
    generation_latency_ms = Column(Float, default=0)
    total_latency_ms = Column(Float, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0)
    
    # Thêm cờ đánh dấu nếu bị Guardrail chặn
    blocked_by_guardrail = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"
    id = Column(String, primary_key=True, default=lambda: generate_id("ret"))
    request_id = Column(String, ForeignKey("rag_request_logs.id"))
    chunk_id = Column(String) # ID bên Qdrant
    score = Column(Float)
    rank = Column(Integer)

class EvaluationScore(Base):
    __tablename__ = "evaluation_scores"
    id = Column(String, primary_key=True, default=lambda: generate_id("eval"))
    request_id = Column(String, ForeignKey("rag_request_logs.id"))
    faithfulness = Column(Float, nullable=True)
    context_precision = Column(Float, nullable=True)
    answer_relevancy = Column(Float, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now())

class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"
    id = Column(String, primary_key=True, default=lambda: generate_id("sum"))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    summary = Column(Text, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

class MemoryFact(Base):
    __tablename__ = "memory_facts"
    id = Column(String, primary_key=True, default=lambda: generate_id("fact"))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    content = Column(Text, nullable=False)
    importance_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SemanticCache(Base):
    __tablename__ = "semantic_cache"
    id = Column(String, primary_key=True, default=lambda: generate_id("cache"))
    query = Column(String, unique=True, index=True)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(String, primary_key=True, default=lambda: generate_id("chunk"))
    source = Column(String, index=True)
    section = Column(String)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
