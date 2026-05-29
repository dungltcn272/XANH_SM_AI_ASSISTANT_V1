import re
import unicodedata
from typing import Dict, Any

class XanhSMGateway:
    """
    Conversation Gateway for Phase 3:
    - Normalizes user input (removes extra spaces, normalizes Vietnamese Unicode NFC)
    - Detects simple languages (Vietnamese vs English)
    - Performs safety precheck (regex patterns and banned keywords) to block spam and sensitive content.
    """
    
    def __init__(self):
        # Banned Vietnamese sensitive/rude keywords (Guardrails)
        self.banned_keywords = [
            "đụ", "đéo", "lồn", "buồi", "cặc", "chịch", "địt", "đm", "vcl", "vkl",
            "chó đẻ", "mẹ kiếp", "đầu khấc", "ăn cứt", "ngu lồn", "đồ chó", "đồ ngu",
            "phản động", "biểu tình", "bạo loạn", "lật đổ chính quyền", "cướp chính quyền",
            "mai linh", "vinasun", "grab", "gojek", "be group", "be car", "bebike",
            "đối thủ bẩn", "cạnh tranh bẩn", "dìm hàng Xanh SM", "lừa đảo khách hàng"
        ]
        
        # Compile safety regex pattern
        pattern_str = "|".join([rf"\b{re.escape(word)}\b" for word in self.banned_keywords])
        self.safety_pattern = re.compile(pattern_str, re.IGNORECASE)

    def normalize_input(self, text: str) -> str:
        """
        Cleans and normalizes Vietnamese text.
        Converts to NFC unicode form and strips excessive spaces.
        """
        if not text:
            return ""
        # Normalize Unicode to NFC (canonical decomposition followed by canonical composition)
        normalized = unicodedata.normalize("NFC", text)
        # Strip excessive spaces
        cleaned = re.sub(r"\s+", " ", normalized).strip()
        return cleaned

    def language_detect(self, text: str) -> str:
        """
        Lightweight language detector.
        Returns 'vi' for Vietnamese, 'en' for English.
        """
        if not text:
            return "vi"
        
        text_lower = text.lower()
        # Common English stop words
        english_words = {"the", "a", "an", "is", "are", "was", "were", "what", "how", "why", "where", "who", "which", "booking", "refund", "driver", "policy"}
        # Common Vietnamese unique characters or words
        vietnamese_indicators = {"đ", "á", "à", "ả", "ã", "ạ", "ấ", "ầ", "ẩ", "ẫ", "ậ", "ớ", "ờ", "ở", "ỡ", "ợ", "ứ", "ừ", "ử", "ữ", "ự", "ê", "ô", "ơ", "ư", "hỏi", "chào", "tài", "xế", "hủy", "phí", "xe"}
        
        words = set(re.findall(r"\b\w+\b", text_lower))
        
        # Count overlaps
        en_count = len(words.intersection(english_words))
        vi_count = 0
        for word in words:
            if any(char in vietnamese_indicators for char in word):
                vi_count += 1
            if word in {"chao", "toi", "xe", "huy", "phi", "tai", "xe", "anh", "chi", "ban"}:
                vi_count += 1
                
        if en_count > vi_count:
            return "en"
        return "vi"

    def safety_precheck(self, text: str) -> Dict[str, Any]:
        """
        Performs robust rule-based safety precheck.
        Blocks vulgar words, political issues, and competitor direct comparison attacks.
        """
        if not text:
            return {"safe": True, "reason": "Empty query"}
            
        text_normalized = self.normalize_input(text)
        
        # Check against regex pattern
        match = self.safety_pattern.search(text_normalized)
        if match:
            matched_word = match.group(0)
            return {
                "safe": False,
                "reason": f"Phát hiện nội dung nhạy cảm hoặc vi phạm chính sách cộng đồng (từ khóa: '{matched_word}')."
            }
            
        # Specific spam check (excessive characters or repeats)
        if len(text_normalized) > 1000:
            return {
                "safe": False,
                "reason": "Độ dài câu hỏi vượt quá giới hạn cho phép (Spam guard)."
            }
            
        # check repetition of a single character
        char_repeats = re.findall(r"(.)\1{9,}", text_normalized)
        if char_repeats:
            return {
                "safe": False,
                "reason": "Phát hiện ký tự lặp lại quá nhiều lần (Spam guard)."
            }

        return {"safe": True, "reason": "Safe"}

    def is_greeting_or_thanks(self, query: str) -> Dict[str, Any]:
        """
        Spell-tolerant and accent-insensitive detector for greetings, thanks, and short chit-chat.
        """
        import unicodedata
        import re

        q_clean = query.strip().lower()
        q_clean = re.sub(r"[\?\!\.\,]", "", q_clean).strip()

        nfkd_form = unicodedata.normalize('NFKD', q_clean)
        q_no_accent = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

        greeting_phrases = {
            "hello", "hi", "halo", "hey", "hola", "hiii", "helloo", "heloo", "helooo",
            "xin chao", "xinchao", "chao ban", "chao", "chao ad", "ad oi", "chao em",
            "chao anh", "chao chi", "chao ban nhe", "chao ban", "chao buoi sang",
            "chao buoi trua", "chao buoi chieu", "chao buoi toi"
        }
        thanks_phrases = {
            "cam on", "camon", "cam on nhieu", "cam on ban", "cam on rat nhieu",
            "thank you", "thanks", "tks", "thks", "ty", "thank"
        }
        farewell_phrases = {
            "tam biet", "tam biet nhe", "goodbye", "bye", "see you", "hen gap lai"
        }

        tokens = q_no_accent.split()
        is_short = len(tokens) <= 6

        is_greet = any(q_no_accent == phrase or q_no_accent.startswith(phrase + " ") or phrase in q_no_accent for phrase in greeting_phrases) and is_short
        is_thank = any(phrase in q_no_accent for phrase in thanks_phrases) and is_short
        is_farewell = any(phrase in q_no_accent for phrase in farewell_phrases) and is_short

        if not (is_greet or is_thank or is_farewell):
            if len(tokens) <= 4:
                if any(token in {"chao", "xin", "hello", "hi", "hey", "alo", "alo", "ok", "oke"} for token in tokens):
                    is_greet = True
                if any(token in {"camon", "thanks", "thank", "tks", "thks", "ty"} for token in tokens):
                    is_thank = True
                if any(token in {"bye", "tam", "goodbye"} for token in tokens):
                    is_farewell = True

        if is_greet and len(tokens) > 5:
            is_greet = False
        if is_thank and len(tokens) > 5:
            is_thank = False
        if is_farewell and len(tokens) > 5:
            is_farewell = False

        if is_greet:
            return {
                "type": "greeting",
                "answer": "Xin chào! Tôi là Trợ lý AI CSKH của Xanh SM. Tôi có thể hỗ trợ gì cho quý khách về chính sách, hủy chuyến, phí dịch vụ hoặc quy định hôm nay?"
            }
        if is_thank:
            return {
                "type": "thanks",
                "answer": "Dạ, rất vui được hỗ trợ quý khách! Nếu còn thắc mắc nào khác, xin cứ tiếp tục hỏi nhé."
            }
        if is_farewell:
            return {
                "type": "farewell",
                "answer": "Cảm ơn quý khách đã sử dụng dịch vụ Xanh SM. Chúc quý khách một ngày tốt lành!"
            }

        return {"type": "none", "answer": ""}

if __name__ == "__main__":
    gateway = XanhSMGateway()
    print(gateway.normalize_input("  Xin   chào   ad  "))
    print(gateway.language_detect("How to book a ride?"))
    print(gateway.safety_precheck("Thằng taxi Grab này phục vụ quá tệ hại"))
    print(gateway.safety_precheck("Hủy chuyến xe bị phạt bao nhiêu?"))
