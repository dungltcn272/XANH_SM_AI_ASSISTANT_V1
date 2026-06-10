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
        # Tier 1: Strictly banned (Toxic, Vulgar, Illegal) - Block immediately
        self.strictly_banned = [
            "đụ", "đéo", "lồn", "buồi", "cặc", "chịch", "địt", "đm", "vcl", "vkl",
            "chó đẻ", "mẹ kiếp", "đầu khấc", "ăn cứt", "ngu lồn", "đồ chó", "đồ ngu",
            "phản động", "biểu tình", "bạo loạn", "lật đổ chính quyền", "cướp chính quyền"
        ]
        
        # Tier 2: Competitors - Only block if combined with negative/aggressive keywords
        self.competitors = ["grab", "gojek", "be group", "be car", "bebike", "mai linh", "vinasun"]
        self.negative_context = [
            "tệ", "đắt", "lừa đảo", "kém", "bẩn", "dìm hàng", "đối thủ", "hơn", "thua", 
            "so với", "so sánh", "chửi", "ngu", "yếu", "nát"
        ]
        
        # Compile patterns
        self.strict_pattern = re.compile("|".join([rf"\b{re.escape(w)}\b" for w in self.strictly_banned]), re.IGNORECASE)
        self.competitor_pattern = re.compile("|".join([rf"\b{re.escape(w)}\b" for w in self.competitors]), re.IGNORECASE)
        self.negative_pattern = re.compile("|".join([rf"\b{re.escape(w)}\b" for w in self.negative_context]), re.IGNORECASE)
        negative_no_accent = [self._strip_accents(w).lower() for w in self.negative_context]
        self.negative_no_accent_pattern = re.compile(
            "|".join([rf"\b{re.escape(w)}\b" for w in negative_no_accent]),
            re.IGNORECASE,
        )
        self.benign_risk_context_pattern = re.compile(
            r"("
            r"neu\s+(toi|minh|khach\s+hang|nguoi\s+dung)?\s*(gap|bi|gap\s+phai)|"
            r"(toi|minh|khach\s+hang|nguoi\s+dung)\s+(bi|gap|gap\s+phai)|"
            r"(gap|gap\s+phai|bi)\s+(lua\s+dao|noi\s+xau|chui|lam\s+phien)|"
            r"(phong\s+tranh|tranh|canh\s+bao|xu\s+ly|lam\s+gi|bao\s+cao|khieu\s+nai|lien\s+he|ho\s+tro|bao\s+ve)"
            r")",
            re.IGNORECASE,
        )
        self.malicious_negative_context_pattern = re.compile(
            r"("
            r"boi\s+nho|noi\s+xau|vu\s+khong|dim\s+hang|ha\s+be|"
            r"khong\s+co\s+bang\s+chung|khong\s+can\s+bang\s+chung|"
            r"hay\s+viet|viet\s+mot\s+bai|tao\s+noi\s+dung|"
            r"chui|so\s+sanh|hon|thua"
            r")",
            re.IGNORECASE,
        )
        self.injection_pattern = re.compile(
            r"("
            r"ignore\s+(all\s+)?previous\s+instructions|"
            r"developer\s+mode|"
            r"system\s+prompt|"
            r"api\s*key|"
            r"reveal\s+(instructions|prompt|secrets)|"
            r"bo qua\s+(moi\s+)?(huong dan|quy tac|chi thi)|"
            r"in ra\s+(toan bo\s+)?(system prompt|api key|cau hinh|chi thi)|"
            r"tiet lo\s+(system prompt|api key|cau hinh|huong dan)|"
            r"cau hinh\s+noi bo"
            r")",
            re.IGNORECASE,
        )

    def normalize_input(self, text: str) -> str:
        """
        Cleans and normalizes Vietnamese text.
        Converts to NFC unicode form and strips excessive spaces.
        """
        if not text:
            return ""
        # Normalize Unicode to NFC
        normalized = unicodedata.normalize("NFC", text)
        # Strip excessive spaces
        cleaned = re.sub(r"\s+", " ", normalized).strip()
        return cleaned

    def _strip_accents(self, text: str) -> str:
        nfkd_form = unicodedata.normalize("NFKD", text)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    def safety_precheck(self, text: str) -> Dict[str, Any]:
        """
        Performs contextual safety precheck.
        1. Strictly blocks vulgar/illegal content.
        2. Blocks competitor mentions ONLY if they appear in a negative or comparative context.
        """
        if not text:
            return {"safe": True, "reason": "Empty query"}
            
        text_normalized = self.normalize_input(text)
        text_no_accent = self._strip_accents(text_normalized).lower()
        has_benign_risk_context = bool(self.benign_risk_context_pattern.search(text_no_accent))
        has_malicious_negative_context = bool(self.malicious_negative_context_pattern.search(text_no_accent))

        injection_match = self.injection_pattern.search(text_no_accent)
        if injection_match:
            return {
                "safe": False,
                "reason": "Em không thể chia sẻ system prompt, API key hoặc cấu hình nội bộ của hệ thống."
            }

        if (
            ("boi nho" in text_no_accent or "noi xau" in text_no_accent or "vu khong" in text_no_accent)
            and ("khong co bang chung" in text_no_accent or "khong can bang chung" in text_no_accent or "lua dao" in text_no_accent)
        ):
            return {
                "safe": False,
                "reason": "Em không thể hỗ trợ bôi nhọ hoặc đưa ra cáo buộc không có căn cứ; em chỉ có thể hỗ trợ thông tin trung lập dựa trên nguồn đáng tin cậy."
            }
        
        # 1. Check Strict Banned List
        strict_match = self.strict_pattern.search(text_normalized)
        if strict_match:
            return {
                "safe": False,
                "reason": "Nội dung có từ ngữ chưa phù hợp, nên em xin phép không tiếp tục với câu hỏi này."
            }
            
        # 2. Check Competitors with Context
        comp_match = self.competitor_pattern.search(text_normalized)
        if comp_match:
            neg_match = self.negative_pattern.search(text_normalized) or self.negative_no_accent_pattern.search(text_no_accent)
            if neg_match and (has_malicious_negative_context or not has_benign_risk_context):
                return {
                    "safe": False,
                    "reason": f"Em chưa thể hỗ trợ nội dung so sánh hoặc nhận xét tiêu cực về {comp_match.group(0)}."
                }
            # If competitor mentioned but no negative context, we let it pass.
            # The LLM will handle it gracefully according to system instructions.

        # 3. Spam protection
        if len(text_normalized) > 1000:
            return {"safe": False, "reason": "Câu hỏi đang hơi dài, anh/chị vui lòng tách thành vài ý ngắn hơn để em hỗ trợ chính xác hơn."}
            
        if re.findall(r"(.)\1{9,}", text_normalized):
            return {"safe": False, "reason": "Tin nhắn có nhiều ký tự lặp lại bất thường, anh/chị vui lòng gửi lại nội dung rõ hơn."}

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

        is_greet = any(re.search(rf'\b{phrase}\b', q_no_accent) for phrase in greeting_phrases) and is_short
        is_thank = any(re.search(rf'\b{phrase}\b', q_no_accent) for phrase in thanks_phrases) and is_short
        is_farewell = any(re.search(rf'\b{phrase}\b', q_no_accent) for phrase in farewell_phrases) and is_short

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
                "answer": "Dạ xin chào! Em là Trợ lý AI CSKH của Xanh SM. Rất vui được gặp anh/chị. Hôm nay em có thể hỗ trợ gì cho mình về các thông tin dịch vụ, chính sách hay quy định của Xanh SM không ạ?"
            }
        if is_thank:
            return {
                "type": "thanks",
                "answer": "Dạ, rất vui được hỗ trợ anh/chị! Nếu mình còn bất kỳ thắc mắc nào khác, xin cứ tiếp tục nhắn em nhé. Chúc anh/chị một ngày tốt lành!"
            }
        if is_farewell:
            return {
                "type": "farewell",
                "answer": "Dạ, cảm ơn anh/chị đã quan tâm và sử dụng dịch vụ của Xanh SM. Hẹn gặp lại anh/chị trong những chuyến đi xanh sắp tới. Chúc mình một ngày tuyệt vời ạ!"
            }

        return {"type": "none", "answer": ""}

if __name__ == "__main__":
    gateway = XanhSMGateway()
    print(gateway.normalize_input("  Xin   chào   ad  "))
    print(gateway.language_detect("How to book a ride?"))
    print(gateway.safety_precheck("Thằng taxi Grab này phục vụ quá tệ hại"))
    print(gateway.safety_precheck("Hủy chuyến xe bị phạt bao nhiêu?"))
