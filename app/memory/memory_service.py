from sqlalchemy.orm import Session
from app.db.models import Message, ConversationSummary, MemoryFact
from datetime import datetime

class MemoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_recent_messages(self, conversation_id: str, limit: int = 12):
        """
        Lấy các message gần nhất từ conversation để dùng làm context cho query rewrite.
        Tăng limit từ 6 lên 12 để có đủ context cho các câu hỏi nối tiếp.
        """
        messages = self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(limit).all()
        return list(reversed(messages))

    def get_conversation_summary(self, conversation_id: str):
        summary = self.db.query(ConversationSummary).filter(ConversationSummary.conversation_id == conversation_id).order_by(ConversationSummary.generated_at.desc()).first()
        return summary.summary if summary else ""

    def get_long_term_memory(self, user_id: str, query: str):
        # TODO: Cần nhúng query (embed), tìm kiếm trong Qdrant để lấy các fact liên quan
        return []

    def save_message(self, conversation_id: str, role: str, content: str):
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg
        
    def extract_and_save_facts(self, user_id: str, content: str):
        # TODO: Dùng LLM để trích xuất fact từ content và lưu vào db & Qdrant
        pass
