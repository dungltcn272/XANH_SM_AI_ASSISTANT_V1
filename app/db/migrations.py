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
        # Bảng: rag_request_logs
        "ALTER TABLE rag_request_logs ADD COLUMN rewrite_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE rag_request_logs ADD COLUMN classification_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE rag_request_logs ADD COLUMN expansion_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE rag_request_logs ADD COLUMN rerank_latency_ms FLOAT DEFAULT 0;",
        "ALTER TABLE rag_request_logs ADD COLUMN blocked_by_guardrail BOOLEAN DEFAULT FALSE;",
        
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
