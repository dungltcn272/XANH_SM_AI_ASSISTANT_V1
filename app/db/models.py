import enum
import uuid
from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Integer, Enum, Boolean
from sqlalchemy.sql import func
from datetime import datetime
import pytz

def get_vn_time():
    return datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))

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
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class GuestSession(Base):
    __tablename__ = "guest_sessions"
    id = Column(String, primary_key=True, default=lambda: generate_id("guest"))
    session_token = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=lambda: generate_id("conv"))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    guest_id = Column(String, ForeignKey("guest_sessions.id"), nullable=True)
    title = Column(String)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: generate_id("msg"))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    pipeline_trace = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class UserReview(Base):
    __tablename__ = "user_reviews"
    id = Column(String, primary_key=True, default=lambda: generate_id("review"))
    message_id = Column(String, ForeignKey("messages.id"), unique=True)
    rating = Column(String, nullable=False)  # 'up' or 'down'

    reason_tags = Column(String, nullable=True)  # JSON string of tags
    comment = Column(Text, nullable=True)
    status = Column(String, default="new", index=True) # 'new', 'reviewed', 'promoted', 'rejected'
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class RagRequestLog(Base):
    __tablename__ = "rag_request_logs"
    id = Column(String, primary_key=True, default=lambda: generate_id("ragreq"))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    user_id = Column(String, nullable=True, index=True)
    guest_id = Column(String, nullable=True, index=True)
    original_query = Column(Text)
    rewritten_query = Column(Text, nullable=True)
    final_answer = Column(Text, nullable=True)
    
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
    
    # Kết quả RAG
    retrieval_result_json = Column(Text, nullable=True)
    rerank_result_json = Column(Text, nullable=True)
    parent_child_result_json = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class BasicRequestLog(Base):
    __tablename__ = "basic_request_logs"
    id = Column(String, primary_key=True, default=lambda: generate_id("basicreq"))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    guest_id = Column(String, nullable=True, index=True)
    original_query = Column(Text, nullable=True)
    rewritten_query = Column(Text, nullable=True)
    intent = Column(String, nullable=True, index=True)
    final_answer = Column(Text, nullable=True)
    model_name = Column(String, nullable=True)
    nlu_latency_ms = Column(Float, default=0)
    total_latency_ms = Column(Float, default=0)
    cost_usd = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), default=get_vn_time, index=True)

class ErrorLog(Base):
    __tablename__ = "error_logs"
    id = Column(String, primary_key=True, default=lambda: generate_id("err"))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    query = Column(Text, nullable=True)
    intent = Column(String, nullable=True)
    error_stage = Column(String, nullable=True, index=True)
    error_cause = Column(Text, nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time, index=True)
class SemanticCache(Base):
    __tablename__ = "semantic_cache"
    id = Column(String, primary_key=True, default=lambda: generate_id("cache"))
    query = Column(String, unique=True, index=True)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(String, primary_key=True, default=lambda: generate_id("chunk"))
    source = Column(String, index=True)
    section = Column(String)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

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
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)

class FoodCatalog(Base):
    __tablename__ = "food_catalog"
    item_id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True, index=True)
    cuisine = Column(String, nullable=True)
    taste_tags_json = Column(Text, nullable=True)
    diet_tags_json = Column(Text, nullable=True)
    ingredient_tags_json = Column(Text, nullable=True)
    price = Column(Integer, nullable=True)
    discount_percent = Column(Integer, nullable=True)
    final_price = Column(Integer, nullable=True)
    currency = Column(String, default="VND")
    image_url = Column(Text, nullable=True)
    merchant_id = Column(String, nullable=True, index=True)
    merchant_name = Column(String, nullable=True, index=True)
    merchant_rating = Column(Float, nullable=True)
    merchant_review_count = Column(Integer, nullable=True)
    merchant_address = Column(Text, nullable=True)
    merchant_lat = Column(Float, nullable=True)
    merchant_lng = Column(Float, nullable=True)
    merchant_open_hours_json = Column(Text, nullable=True)
    avg_prep_minutes = Column(Integer, nullable=True)
    base_delivery_fee = Column(Integer, nullable=True)
    fee_per_km = Column(Integer, nullable=True)
    service_radius_km = Column(Float, nullable=True)
    source = Column(String, default="shopeefood", index=True)
    source_url = Column(Text, nullable=True)
    city = Column(String, nullable=True, index=True)
    city_slug = Column(String, nullable=True, index=True)
    raw_ref = Column(String, nullable=True)
    raw_json = Column(Text, nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    imported_at = Column(DateTime(timezone=True), default=get_vn_time)

class FoodInteraction(Base):
    __tablename__ = "food_interactions"
    event_id = Column(String, primary_key=True, default=lambda: generate_id("foodevt"))
    user_id = Column(String, nullable=True, index=True)
    session_id = Column(String, nullable=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    item_id = Column(String, nullable=True, index=True)
    merchant_id = Column(String, nullable=True, index=True)
    rank_position = Column(Integer, nullable=True)
    query = Column(Text, nullable=True)
    request_context_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time, index=True)

class UserFoodProfile(Base):
    __tablename__ = "user_food_profiles"
    id = Column(String, primary_key=True, default=lambda: generate_id("foodprof"))
    user_id = Column(String, nullable=True, index=True)
    guest_id = Column(String, nullable=True, index=True)
    current_location_json = Column(Text, nullable=True)
    saved_places_json = Column(Text, nullable=True)
    liked_items_json = Column(Text, nullable=True)
    disliked_items_json = Column(Text, nullable=True)
    preferred_categories_json = Column(Text, nullable=True)
    preferred_tags_json = Column(Text, nullable=True)
    avoided_tags_json = Column(Text, nullable=True)
    budget_profile_json = Column(Text, nullable=True)
    allergies_json = Column(Text, nullable=True)
    profile_stats_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time, index=True)

class FoodRequestLog(Base):
    __tablename__ = "food_request_logs"
    trace_id = Column(String, primary_key=True, default=lambda: generate_id("foodreq"))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    guest_id = Column(String, nullable=True, index=True)
    original_query = Column(Text, nullable=True)
    rewritten_query = Column(Text, nullable=True)
    final_answer = Column(Text, nullable=True)
    intent = Column(String, nullable=True, index=True)
    
    # Telemetry
    search_latency_ms = Column(Float, default=0)
    generation_latency_ms = Column(Float, default=0)
    total_latency_ms = Column(Float, default=0)
    rewrite_latency_ms = Column(Float, default=0)
    classification_latency_ms = Column(Float, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0)
    
    # Results
    nlu_json = Column(Text, nullable=True)
    user_context_json = Column(Text, nullable=True)
    location_json = Column(Text, nullable=True)
    candidate_stats_json = Column(Text, nullable=True)
    ranking_json = Column(Text, nullable=True)
    answer_llm_json = Column(Text, nullable=True)
    sse_events_json = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=get_vn_time, index=True)



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
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
