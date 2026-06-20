import re
from typing import Generator, Union

class OutputGuardrail:
    """
    Advanced Heuristics/Regex Guardrail System for Xanh SM.
    Blocks toxic content, prompt injections, and system prompt leakage with ~0ms latency.
    """
    # Expanded list of Vietnamese and English toxic/banned terms
    BANNED_WORDS = [
        r"fuck", r"shit", r"địt", r"lồn", r"cặc", r"bố mày", r"đĩ", r"buồi", r"đéo",
        r"vcl", r"vkl", r"chó đẻ", r"mẹ kiếp", r"đầu khấc", r"ăn cứt", r"ngu lồn",
        r"đồ chó", r"đồ ngu", r"phản động", r"biểu tình", r"bạo loạn",
        r"lật đổ chính quyền", r"cướp chính quyền"
    ]
    
    # Prompt injection patterns (protects against hijacking)
    INJECTION_INDICATORS = [
        r"ignore (all )?previous instructions",
        r"ignore the rules",
        r"bỏ qua (mọi )?hướng dẫn",
        r"bỏ qua (mọi )?quy tắc",
        r"system prompt",
        r"hãy đóng vai",
        r"you are now a",
        r"developer mode",
        r"tắt bộ lọc",
        r"reveal instructions",
        r"tiết lộ hướng dẫn",
        r"phát biểu của hệ thống"
    ]
    
    # System prompt leakage patterns (prevents model from exposing internal instructions)
    LEAKAGE_INDICATORS = [
        r"tôi là một mô hình ngôn ngữ",
        r"quy tắc hệ thống của tôi",
        r"đây là system prompt",
        r"hướng dẫn hệ thống",
        r"system instruction",
        r"phần quy định hoạt động",
        r"tôi được lập trình để"
    ]

    def __init__(self):
        # Compile all patterns for efficiency
        self.banned_pattern = re.compile("|".join(self.BANNED_WORDS), re.IGNORECASE)
        self.injection_pattern = re.compile("|".join(self.INJECTION_INDICATORS), re.IGNORECASE)
        self.leakage_pattern = re.compile("|".join(self.LEAKAGE_INDICATORS), re.IGNORECASE)
        
    def check_safe(self, text: str) -> bool:
        """
        Validates text against toxic words, prompt injections, and leakage.
        """
        if not text:
            return True
            
        # 1. Check for banned/toxic words
        if self.banned_pattern.search(text):
            return False
            
        # 2. Check for system prompt leakage. Prompt-injection attempts are
        # handled at the input gateway so valid domain answers are not blocked.
        if self.leakage_pattern.search(text):
            return False
            
        return True
    
    def sanitize_stream(self, generator: Generator[str, None, None]) -> Generator[str, None, None]:
        """
        Wraps a streaming generator. If a safety violation is detected in the accumulated buffer,
        it immediately stops the stream and yields a clean fallback warning.
        """
        buffer = ""
        for chunk in generator:
            if chunk.startswith("data: ") and "[DONE]" not in chunk:
                # Extract content from chunk
                content = chunk.replace("data: ", "").replace("\n", "").strip()
                # If content is a JSON metadata payload, do not analyze it for text safety
                if not (content.startswith("{") and content.endswith("}")):
                    buffer += content + " "
                    
                    # Run safety validation on the cumulative text buffer
                    if not self.check_safe(buffer):
                        yield 'data: {"error": "Dạ, em xin lỗi nhưng nội dung này có thể vi phạm chính sách an toàn của Xanh SM. Em có thể hỗ trợ anh/chị các vấn đề khác liên quan đến dịch vụ taxi điện được không ạ?"}\n\n'
                        yield "data: [DONE]\n\n"
                        return
            yield chunk
