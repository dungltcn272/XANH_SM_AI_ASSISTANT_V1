import re

class OutputGuardrail:
    """
    Lightweight Heuristics/Regex Guardrail
    Chặn các luồng thông tin không mong muốn hoặc độc hại với độ trễ ~0ms.
    """
    BANNED_WORDS = [
        r"fuck", r"shit", r"địt", r"lồn", r"cặc", 
        r"bố mày", r"đĩ"
    ]
    
    def __init__(self):
        self.pattern = re.compile("|".join(self.BANNED_WORDS), re.IGNORECASE)
        
    def check_safe(self, text: str) -> bool:
        if not text:
            return True
        if self.pattern.search(text):
            return False
        return True
    
    def sanitize_stream(self, generator):
        """
        Wrap một streaming generator. Nếu phát hiện vi phạm, sẽ lập tức dừng 
        và trả về thông báo lỗi.
        """
        buffer = ""
        for chunk in generator:
            if chunk.startswith("data: ") and "[DONE]" not in chunk:
                content = chunk.replace("data: ", "").replace("\n", "").strip()
                buffer += content + " "
                
                # Check heuristic an toàn trên buffer
                if not self.check_safe(buffer):
                    yield 'data: {"error": "Nội dung vi phạm chính sách an toàn của Xanh SM."}\n\n'
                    yield "data: [DONE]\n\n"
                    return
            yield chunk
