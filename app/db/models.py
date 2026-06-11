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
    pipeline_trace = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserReview(Base):
    __tablename__ = "user_reviews"
    id = Column(String, primary_key=True, default=lambda: generate_id("review"))
    message_id = Column(String, ForeignKey("messages.id"), unique=True)
    rating = Column(String, nullable=False)  # 'up' or 'down'
    reason_tags = Column(String, nullable=True)  # JSON string of tags
    comment = Column(Text, nullable=True)
    status = Column(String, default="new", index=True) # 'new', 'reviewed', 'promoted', 'rejected'
    admin_note = Column(Text, nullable=True)
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
    rewrite_latency_ms = Column(Float, default=0)
    classification_latency_ms = Column(Float, default=0)
    expansion_latency_ms = Column(Float, default=0)
    rerank_latency_ms = Column(Float, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0)
    
    # Thêm cờ đánh dấu nếu bị Guardrail chặn
    blocked_by_guardrail = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"
    id = Column(String, primary_key=True, default=lambda: generate_id("sum"))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    summary = Column(Text, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
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

class CrawlSource(Base):
    __tablename__ = "crawl_sources"
    id = Column(String, primary_key=True, default=lambda: generate_id("crawlsrc"))
    url = Column(Text, nullable=False)
    title = Column(String, nullable=True)
    source_profile = Column(String, index=True, default="main_site")
    source_type = Column(String, index=True, default="web")
    category = Column(String, index=True, default="user")
    document_type = Column(String, index=True, default="service")
    output_dir = Column(String, default="data/user")
    crawl_strategy = Column(String, default="default")
    enabled = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=100)
    notes = Column(Text, nullable=True)
    last_crawled_at = Column(DateTime(timezone=True), nullable=True)
    last_status = Column(String, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SystemLog(Base):
    __tablename__ = "system_logs"
    id = Column(String, primary_key=True, default=lambda: generate_id("log"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    level = Column(String, nullable=False)
    phase = Column(String, nullable=False)
    error_type = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id = Column(String, primary_key=True, default=lambda: generate_id("evalrun"))
    run_name = Column(String, index=True, nullable=False)
    dataset_name = Column(String, default="golden_50")
    model_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    total_cases = Column(Integer, default=0)
    status = Column(String, default="completed", index=True)
    average_latency_sec = Column(Float, default=0)
    recall_5 = Column(Float, default=0)
    recall_10 = Column(Float, default=0)
    mrr = Column(Float, default=0)
    ndcg_5 = Column(Float, default=0)
    faithfulness = Column(Float, default=0)
    correctness = Column(Float, default=0)
    relevancy = Column(Float, default=0)
    metrics_json = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

