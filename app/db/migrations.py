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
