from sqlalchemy.orm import Session
from app.rag.chain import XanhSMRAGPipeline
from app.memory.memory_service import MemoryService
from app.db.models import RagRequestLog
from app.rag.guardrail import OutputGuardrail
from app.core.logger import log_info, log_warn
import json

def stream_chat_pipeline(db: Session, user_id: str, conversation_id: str, question: str, role: str = "faq"):
    """
    Kết nối Endpoint `/chat` với NLU-Gateway Pipeline (Phase 4).
    Sử dụng XanhSMRAGPipeline để stream text theo định dạng SSE.
    
    Tracks và saves:
    - rewritten_query: Câu hỏi được viết lại dựa trên context
    - search_latency_ms: Thời gian tìm kiếm tài liệu
    - generation_latency_ms: Thời gian LLM synthesis
    - total_latency_ms: Tổng thời gian
    - total_tokens: Tổng số tokens (estimated)
    - cost_usd: Chi phí API
    """
    # Lấy lịch sử 3 lượt gần nhất
    memory_service = MemoryService(db)
    raw_history = memory_service.get_recent_messages(conversation_id, limit=12)  # Increased from 6 to 12
    chat_history = [{"role": msg.role, "content": msg.content} for msg in raw_history]
    
    # Close database session immediately to release PostgreSQL/SQLite connection,
    # preventing socket conflicts with Qdrant/OpenAI and connection hogging during RAG
    db.close()
    try:
        from app.db.database import engine
        engine.dispose()
    except Exception:
        pass
    
    # Init Pipeline
    pipeline = XanhSMRAGPipeline()
    guardrail = OutputGuardrail()
    
    final_answer = ""
    is_blocked = False
    rewritten_query = ""
    metrics = {
        "search_latency_ms": 0,
        "generation_latency_ms": 0,
        "total_latency_ms": 0,
        "total_tokens": 0,
        "cost_usd": 0.0
    }
    
    # First yield conversation_id so frontend can track history
    yield f'data: {{"conversation_id": "{conversation_id}"}}\n\n'
    
    # Chạy streaming qua Guardrail
    for event in guardrail.sanitize_stream(pipeline.stream_run(query=question, role=role, chat_history=chat_history)):
        if "Nội dung vi phạm" in event:
            is_blocked = True
            final_answer = "Nội dung vi phạm chính sách an toàn của Xanh SM."
        elif event.startswith("data: ") and "[DONE]" not in event:
            # Extract raw token content (preserving exact spacing and newlines)
            raw_event = event[6:]  # Strip "data: "
            if raw_event.endswith("\n\n"):
                raw_event = raw_event[:-2]
            elif raw_event.endswith("\n"):
                raw_event = raw_event[:-1]
            
            # Try to parse as JSON to extract metrics
            try:
                data_obj = json.loads(raw_event)
                if isinstance(data_obj, dict) and "metrics" in data_obj:
                    if "rewritten_query" in data_obj["metrics"]:
                        rewritten_query = data_obj["metrics"]["rewritten_query"]
                    metrics.update(data_obj["metrics"])
            except (json.JSONDecodeError, TypeError):
                # Not JSON, accumulate directly
                final_answer += raw_event
        
        yield event
    
    # Open a fresh database session to save results safely
    from app.db.database import SessionLocal
    new_db = SessionLocal()
    try:
        new_memory_service = MemoryService(new_db)
        # Save user message to DB
        new_memory_service.save_message(conversation_id, "user", question)
        
        # Lưu câu trả lời vào DB
        if final_answer:
            new_memory_service.save_message(conversation_id, "assistant", final_answer.strip())
            
            # Log request with metrics
            try:
                from app.core.config import settings
                req_log = RagRequestLog(
                    conversation_id=conversation_id,
                    original_query=question,
                    rewritten_query=rewritten_query or question,  # Use original query if rewrite failed
                    final_answer=final_answer.strip(),
                    search_latency_ms=metrics.get("search_latency_ms", 0),
                    generation_latency_ms=metrics.get("generation_latency_ms", 0),
                    total_latency_ms=metrics.get("total_latency_ms", 0),
                    rewrite_latency_ms=metrics.get("rewrite_latency_ms", 0),
                    classification_latency_ms=metrics.get("classification_latency_ms", 0),
                    expansion_latency_ms=metrics.get("expansion_latency_ms", 0),
                    rerank_latency_ms=metrics.get("rerank_latency_ms", 0),
                    total_tokens=metrics.get("total_tokens", 0),
                    cost_usd=metrics.get("cost_usd", 0.0),
                    blocked_by_guardrail=is_blocked,
                    intent=metrics.get("intent", "rag")
                )
                new_db.add(req_log)
                new_db.commit()
                log_info("CHAT", f"Saved request log with metrics - Latency: {metrics.get('total_latency_ms', 0):.0f}ms (Rewrite: {metrics.get('rewrite_latency_ms', 0):.0f}ms, Classify: {metrics.get('classification_latency_ms', 0):.0f}ms, Expand: {metrics.get('expansion_latency_ms', 0):.0f}ms, Search: {metrics.get('search_latency_ms', 0):.0f}ms, Rerank: {metrics.get('rerank_latency_ms', 0):.0f}ms, Gen: {metrics.get('generation_latency_ms', 0):.0f}ms), Chunks: {metrics.get('num_chunks_before_expansion', 0)}, ContextLen: {metrics.get('compressed_context_len', 0)}, Tokens: {metrics.get('total_tokens', 0)}, Cost: ${metrics.get('cost_usd', 0):.6f}")
            except Exception as e:
                log_warn("CHAT", f"Failed to log request: {e}")
                new_db.rollback()
    finally:
        new_db.close()
        try:
            from app.db.database import engine
            engine.dispose()
        except Exception:
            pass
