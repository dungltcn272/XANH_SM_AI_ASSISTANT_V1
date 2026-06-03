from langchain_openai import OpenAIEmbeddings
from app.core.config import settings

def get_embedding_model():
    """
    Khởi tạo OpenAI Embedding Model (mặc định dùng text-embedding-3-small).
    Có thể cấu hình lại nếu dùng mô hình khác.
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY chưa được cấu hình!")
        
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.OPENAI_API_KEY
    )
