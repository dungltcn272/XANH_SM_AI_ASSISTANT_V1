import logging
from sqlalchemy import text
from app.db.database import engine
import logging
from sqlalchemy import text
from app.db.database import engine

logger = logging.getLogger(__name__)

def run_auto_migrations():
    """
    Tự động chạy các lệnh ALTER TABLE để đảm bảo Database schema được cập nhật.
    Nếu bảng/cột đã tồn tại, lỗi sẽ được bỏ qua.
    """
    queries = [
        # Bảng: rag_request_logs (Thêm các cột mới)
        "ALTER TABLE rag_request_logs ADD COLUMN rewrite_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE rag_request_logs ADD COLUMN classification_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE rag_request_logs ADD COLUMN expansion_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE rag_request_logs ADD COLUMN rerank_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE rag_request_logs ADD COLUMN blocked_by_guardrail BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE rag_request_logs ADD COLUMN user_id VARCHAR;",
        "ALTER TABLE rag_request_logs ADD COLUMN guest_id VARCHAR;",
        "ALTER TABLE rag_request_logs ADD COLUMN retrieval_result_json TEXT;",
        "ALTER TABLE rag_request_logs ADD COLUMN rerank_result_json TEXT;",
        "ALTER TABLE rag_request_logs ADD COLUMN parent_child_result_json TEXT;",
        "ALTER TABLE rag_request_logs DROP COLUMN intent;",
        "CREATE INDEX IF NOT EXISTS ix_rag_request_logs_user_id ON rag_request_logs(user_id);",
        "CREATE INDEX IF NOT EXISTS ix_rag_request_logs_guest_id ON rag_request_logs(guest_id);",
        
        # Xóa các bảng cũ
        "DROP TABLE IF EXISTS system_logs;",
        "DROP TABLE IF EXISTS conversation_summaries;",
        
        # Bảng mới: error_logs
        """
        CREATE TABLE IF NOT EXISTS error_logs (
            id VARCHAR PRIMARY KEY,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            query TEXT,
            intent VARCHAR,
            error_stage VARCHAR,
            error_cause VARCHAR,
            message TEXT NOT NULL,
            details TEXT
        );
        """,
        
        # Bảng mới: basic_request_logs
        """
        CREATE TABLE IF NOT EXISTS basic_request_logs (
            id VARCHAR PRIMARY KEY,
            conversation_id VARCHAR REFERENCES conversations(id),
            user_id VARCHAR,
            guest_id VARCHAR,
            original_query TEXT,
            rewritten_query TEXT,
            intent VARCHAR,
            final_answer TEXT,
            nlu_latency_ms FLOAT DEFAULT 0,
            total_latency_ms FLOAT DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_basic_request_logs_conversation_id ON basic_request_logs(conversation_id);",
        "CREATE INDEX IF NOT EXISTS ix_basic_request_logs_user_id ON basic_request_logs(user_id);",
        "CREATE INDEX IF NOT EXISTS ix_basic_request_logs_guest_id ON basic_request_logs(guest_id);",
        "CREATE INDEX IF NOT EXISTS ix_basic_request_logs_intent ON basic_request_logs(intent);",
        "CREATE INDEX IF NOT EXISTS ix_basic_request_logs_created_at ON basic_request_logs(created_at);",
        "ALTER TABLE basic_request_logs ADD COLUMN nlu_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE basic_request_logs ADD COLUMN model_name VARCHAR;",
        "ALTER TABLE basic_request_logs ADD COLUMN cost_usd FLOAT DEFAULT 0;",
        
        # Đổi tên và sửa bảng food_recommendation_traces thành food_request_logs
        "ALTER TABLE food_recommendation_traces RENAME TO food_request_logs;",
        "ALTER TABLE food_request_logs ADD COLUMN final_answer TEXT;",
        "ALTER TABLE food_request_logs ADD COLUMN search_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE food_request_logs ADD COLUMN generation_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE food_request_logs ADD COLUMN total_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE food_request_logs ADD COLUMN rewrite_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE food_request_logs ADD COLUMN classification_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE food_request_logs ADD COLUMN total_tokens INTEGER DEFAULT 0;",
        "ALTER TABLE food_request_logs ADD COLUMN cost_usd FLOAT DEFAULT 0;",
        
        # Bảng: messages
        "ALTER TABLE messages ADD COLUMN pipeline_trace TEXT;",
        
        # Bảng: evaluation_runs
        "ALTER TABLE evaluation_runs ADD COLUMN description TEXT;",
        "ALTER TABLE food_catalog ADD COLUMN city VARCHAR;",
        "ALTER TABLE food_catalog ADD COLUMN city_slug VARCHAR;",
        """
        CREATE TABLE IF NOT EXISTS food_interactions (
            event_id VARCHAR PRIMARY KEY,
            user_id VARCHAR,
            session_id VARCHAR,
            conversation_id VARCHAR REFERENCES conversations(id),
            message_id VARCHAR REFERENCES messages(id),
            event_type VARCHAR NOT NULL,
            item_id VARCHAR,
            merchant_id VARCHAR,
            rank_position INTEGER,
            query TEXT,
            request_context_json TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_food_interactions_user_id ON food_interactions(user_id);",
        "CREATE INDEX IF NOT EXISTS ix_food_interactions_session_id ON food_interactions(session_id);",
        "CREATE INDEX IF NOT EXISTS ix_food_interactions_conversation_id ON food_interactions(conversation_id);",
        "CREATE INDEX IF NOT EXISTS ix_food_interactions_message_id ON food_interactions(message_id);",
        "CREATE INDEX IF NOT EXISTS ix_food_interactions_event_type ON food_interactions(event_type);",
        "CREATE INDEX IF NOT EXISTS ix_food_interactions_item_id ON food_interactions(item_id);",
        "CREATE INDEX IF NOT EXISTS ix_food_interactions_merchant_id ON food_interactions(merchant_id);",
        "CREATE INDEX IF NOT EXISTS ix_food_interactions_created_at ON food_interactions(created_at);",
        "ALTER TABLE food_interactions DROP CONSTRAINT IF EXISTS food_interactions_item_id_fkey;",
        """
        CREATE TABLE IF NOT EXISTS user_food_profiles (
            id VARCHAR PRIMARY KEY,
            user_id VARCHAR,
            guest_id VARCHAR,
            current_location_json TEXT,
            saved_places_json TEXT,
            liked_items_json TEXT,
            disliked_items_json TEXT,
            preferred_categories_json TEXT,
            preferred_tags_json TEXT,
            avoided_tags_json TEXT,
            budget_profile_json TEXT,
            allergies_json TEXT,
            profile_stats_json TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_user_food_profiles_user_id ON user_food_profiles(user_id);",
        "CREATE INDEX IF NOT EXISTS ix_user_food_profiles_guest_id ON user_food_profiles(guest_id);",
        "CREATE INDEX IF NOT EXISTS ix_user_food_profiles_updated_at ON user_food_profiles(updated_at);",
    ]
    
    with engine.connect() as conn:
        for query in queries:
            try:
                conn.execute(text(query))
                conn.commit()
                logger.info(f"Migration Success: {query}")
            except Exception as e:
                # Phải rollback transaction nếu gặp lỗi (đặc biệt quan trọng với PostgreSQL)
                conn.rollback()
                pass
                
    logger.info("Auto migrations completed.")
