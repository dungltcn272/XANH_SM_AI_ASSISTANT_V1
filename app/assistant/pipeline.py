from sqlalchemy.orm import Session
from app.assistant.orchestrator import XanhSMAssistantOrchestrator
from app.memory.memory_service import MemoryService
from app.db.models import RagRequestLog
from app.rag.guardrail import OutputGuardrail
from app.core.logger import log_info, log_warn
import json

def stream_chat_pipeline(db: Session, user_id: str, conversation_id: str, question: str, image_base64: str = None, is_deep_search: bool = False, entity_type: str = "anonymous", display_query: str = None):
    # Lấy lịch sử 3 lượt gần nhất
    memory_service = MemoryService(db)
    raw_history = memory_service.get_recent_messages(conversation_id, limit=12)  # Increased from 6 to 12
    chat_history = [{"role": msg.role, "content": msg.content} for msg in raw_history]
    try:
        from app.food_recommendation.profile_store import food_profile_context
        food_context = food_profile_context(
            db=db,
            user_id=user_id if entity_type == "user" else None,
            guest_id=user_id if entity_type == "guest" else None,
        )
    except Exception as exc:
        log_warn("CHAT", f"Failed to load food profile context: {exc}")
        food_context = None
    
    # Close database session immediately to release PostgreSQL/SQLite connection,
    # preventing socket conflicts with Qdrant/OpenAI and connection hogging during RAG
    db.close()
    try:
        from app.db.database import engine
        engine.dispose()
    except Exception:
        pass
    
    # Init Pipeline
    pipeline = XanhSMAssistantOrchestrator()
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
    for event in guardrail.sanitize_stream(pipeline.stream_run(
        query=question,
        chat_history=chat_history,
        image_base64=image_base64,
        is_deep_search=is_deep_search,
        food_context=food_context,
        conversation_id=conversation_id,
        user_id=user_id if entity_type == "user" else None,
        guest_id=user_id if entity_type == "guest" else None,
    )):
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
        new_memory_service.save_message(conversation_id, "user", display_query or question)
        
        # Tự động tạo tiêu đề cuộc hội thoại nếu chưa có
        conv = new_db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv and (not conv.title or conv.title.strip() == "" or conv.title == "New Conversation"):
            words = (display_query or question).strip().split()
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
            msg = new_memory_service.save_message(conversation_id, "assistant", final_answer.strip())
            msg.pipeline_trace = json.dumps(metrics, ensure_ascii=False)
            new_db.commit()
            
            # Gửi message_id về cho frontend
            yield f'data: {{"message_id": "{msg.id}"}}\n\n'
            
            # Centralized logging for ALL intents
            intent_to_save = "blocked_guardrail" if is_blocked else metrics.get('intent', 'unknown')
            from app.assistant.trace_store import save_basic_request_log
            save_basic_request_log(
                conversation_id=conversation_id,
                user_id=user_id if entity_type == "user" else None,
                guest_id=user_id if entity_type == "guest" else None,
                original_query=display_query or question,
                rewritten_query=rewritten_query or question,
                intent=intent_to_save,
                final_answer=final_answer.strip(),
                nlu_latency_ms=metrics.get('rewrite_latency_ms', 0),
                total_latency_ms=metrics.get('total_latency_ms', 0),
                model_name=metrics.get('answer_model') or metrics.get('model_name'),
                cost_usd=metrics.get('cost_usd', 0.0)
            )
            
            log_info("CHAT", f"Finished pipeline execution for conversation: {conversation_id}, Intent: {intent_to_save}")
    finally:
        new_db.close()
        try:
            from app.db.database import engine
            engine.dispose()
        except Exception:
            pass
