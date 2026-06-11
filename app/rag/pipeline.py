from sqlalchemy.orm import Session
from app.rag.chain import XanhSMRAGPipeline
from app.memory.memory_service import MemoryService
from app.db.models import RagRequestLog
from app.rag.guardrail import OutputGuardrail
from app.core.logger import log_info, log_warn
import json

def stream_chat_pipeline(db: Session, user_id: str, conversation_id: str, question: str, image_base64: str = None):
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
    for event in guardrail.sanitize_stream(pipeline.stream_run(query=question, chat_history=chat_history, image_base64=image_base64)):
        if "Nội dung vi phạm" in event:
            is_blocked = True
            final_answer = "Dạ, em xin lỗi nhưng nội dung này có thể vi phạm chính sách an toàn của Xanh SM. Em có thể hỗ trợ anh/chị các vấn đề khác liên quan đến dịch vụ taxi điện được không ạ?"
        elif event.startswith("data: ") and "[DONE]" not in event:
            # Extract raw token content (preserving exact spacing and newlines)
            # An event can contain multiple lines, each starting with "data: " due to newlines
            lines = event.split("\n")
            event_content_parts = []
            for line in lines:
                if line.startswith("data: "):
                    line_data = line[6:]
                    if line_data == "[DONE]":
                        continue
                    event_content_parts.append(line_data)
                elif line.strip() == "":
                    continue
                else:
                    event_content_parts.append(line)
            
            raw_event = "\n".join(event_content_parts)
            
            # Try to parse as JSON to extract metrics. We only consider it as JSON
            # if it starts and ends with curly braces (indicating a JSON object for metadata).
            # This prevents raw text tokens like pure numbers or boolean values (e.g. "270", "30", "true")
            # from being incorrectly parsed as valid JSON and dropped from the final saved answer.
            is_json_metadata = False
            if raw_event.strip().startswith("{") and raw_event.strip().endswith("}"):
                try:
                    data_obj = json.loads(raw_event)
                    if isinstance(data_obj, dict):
                        is_json_metadata = True
                        if "metrics" in data_obj:
                            if "rewritten_query" in data_obj["metrics"]:
                                rewritten_query = data_obj["metrics"]["rewritten_query"]
                            metrics.update(data_obj["metrics"])
                except (json.JSONDecodeError, TypeError):
                    pass
            
            if not is_json_metadata:
                final_answer += raw_event
        
        yield event
    
    # Open a fresh database session to save results safely
    from app.db.database import SessionLocal
    from app.db.models import Conversation
    new_db = SessionLocal()
    try:
        new_memory_service = MemoryService(new_db)
        # Save user message to DB
        new_memory_service.save_message(conversation_id, "user", question)
        
        # Tự động tạo tiêu đề cuộc hội thoại nếu chưa có
        conv = new_db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv and (not conv.title or conv.title.strip() == "" or conv.title == "New Conversation"):
            words = question.strip().split()
            title_words = words[:6]
            title = " ".join(title_words)
            # Viết hoa chữ cái đầu của mỗi từ cho đẹp
            title = " ".join(w.capitalize() for w in title.split())
            if len(words) > 6:
                title += "..."
            conv.title = title
            new_db.commit()
        
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
