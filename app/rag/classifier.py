import json
import re
import unicodedata
from typing import Dict, Any, List, Tuple, Optional
from openai import OpenAI
from app.core.config import settings as config
from app.rag.prompt import UNIFIED_NLU_PROMPT
from app.rag.domain_vocabulary import enrich_queries, understand_query
from app.core.logger import log_warn

class XanhSMClassifier:
    """
    Unified Intent Classifier & Query Rewriter & Query Expander Gateway.
    """
    
    def __init__(self):
        pass

    def _strip_accents(self, text: str) -> str:
        normalized = unicodedata.normalize("NFD", text or "")
        return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()

    def _needs_context_rewrite(self, query: str, chat_history: List[Dict[str, str]] = None) -> bool:
        if not chat_history:
            return False
        q = self._strip_accents(query)
        reference_patterns = [
            r"\b(no|nay|do|kia|tren|duoi|cai nay|cai do|van de nay|muc nay|phan nay)\b",
            r"\b(con|the|vay|nhu vay|doi voi no|truong hop do)\b",
            r"^\s*(con|vay|the)\b",
        ]
        return any(re.search(pattern, q) for pattern in reference_patterns)

    def _is_obvious_rag_query(self, query: str) -> bool:
        q = self._strip_accents(query)
        domain_understanding = understand_query(query)
        strong_domain_signal = bool(domain_understanding.services and domain_understanding.intents)
        if len(q.strip()) < config.NLU_FAST_PATH_MIN_CHARS and not strong_domain_signal:
            return False

        domain_terms = [
            "xanh sm", "xsm", "gsm", "green sm", "vinfast", "v-green", "v green", "vgreen", "vf ", "vf3", "vf 3",
            "vf5", "vf 5", "vf6", "vf 6", "vf7", "vf 7", "herio", "limo", "ec van",
            "xe may dien", "o to dien", "taxi", "bike", "platform", "platfom", "merchant",
            "tai xe", "tx", "bac tai", "doi tac", "khach hang", "mua xe", "thue pin",
            "sac", "tram sac", "doi pin", "pin", "bao hiem", "boi thuong", "den hang",
            "hoan tien", "huy chuyen", "cuoc", "gia", "phi", "uu dai", "vay von", "free",
            "chinh sach", "dieu kien", "quy dinh", "thuong", "doanh thu",
            "chiet khau", "ho so", "dang ky", "dk", "hop dong", "khuyen mai"
        ]
        question_terms = [
            "bao nhieu", "la gi", "nhu the nao", "co khong", "dieu kien", "chinh sach",
            "so sanh", "ap dung", "can gi", "duoc gi", "tu khi nao", "den nam", "muc nao",
            "bn", "ntn", "khac j", "khac gi", "the nao", "ra sao", "la sao"
        ]
        has_domain_signal = any(term in q for term in domain_terms) or bool(
            domain_understanding.services or domain_understanding.intents
        )
        return has_domain_signal and (
            any(term in q for term in question_terms) or "?" in query or len(q.split()) >= 8
        )

    def _fast_rag_nlu(self, query: str) -> Dict[str, Any]:
        expanded = [query]
        return {
            "rewritten_query": query,
            "intent": "rag",
            "expanded_queries": expanded[:8],
            "suggested_answer": None,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            "fast_path": True,
            "fast_path_reason": "obvious_rag_query"
        }

    def unified_nlu(self, query: str, chat_history: List[Dict[str, str]] = None, image_base64: str = None) -> Dict[str, Any]:
        """
        Unified 3-in-1 NLU Analyzer:
        1. Context-aware rewrite
        2. Intent classification (rag, small-talk)
        3. Query expansion
        """
        query_lower = query.lower()
        
        # Rule-based safety triggers (fast early exit for sensitive words)
        from app.rag.gateway import XanhSMGateway
        gateway = XanhSMGateway()
        safety_res = gateway.safety_precheck(query)
        if not safety_res["safe"]:
            return {
                "rewritten_query": query,
                "intent": "sensitive", # Blocked immediately by gateway rule
                "expanded_queries": [query],
                "safety_blocked": True,
                "safety_reason": safety_res["reason"],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "fast_path": True,
                "fast_path_reason": "safety_rule"
            }

        # Rule-based Small-talk fast check (exact matches or very short phrases)
        greeting_check = gateway.is_greeting_or_thanks(query)
        if greeting_check["type"] != "none":
            return {
                "rewritten_query": query,
                "intent": "small-talk",
                "expanded_queries": [query],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "fast_path": True,
                "fast_path_reason": "small_talk_rule"
            }

        if (
            config.NLU_FAST_PATH_ENABLED
            and not image_base64
            and self._is_obvious_rag_query(query)
            and not self._needs_context_rewrite(query, chat_history)
        ):
            return self._fast_rag_nlu(query)

        # If LLM is available, use it for NLU
        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                history_str = ""
                if chat_history:
                    # Keep only last 3 turns to keep context compact and focus NLU
                    for turn in chat_history[-3:]:
                        role_tag = "User" if turn.get("role") == "user" else "Assistant"
                        history_str += f"{role_tag}: {turn.get('content')}\n"

                client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.OPENAI_TIMEOUT_SECONDS)
                user_prompt = f"Lịch sử hội thoại:\n{history_str}\nCâu hỏi mới nhất: '{query}'\nJSON kết quả:"
                if image_base64:
                    user_content = [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                else:
                    user_content = user_prompt

                response = client.chat.completions.create(
                    model=config.NLU_MODEL,
                    messages=[
                        {"role": "system", "content": UNIFIED_NLU_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.0,
                    max_tokens=220,
                    response_format={"type": "json_object"}
                )
                res_content = response.choices[0].message.content.strip()
                # Cleanup potential markdown blocks
                res_content = re.sub(r"```json|```", "", res_content).strip()
                result = json.loads(res_content)
                
                # Normalize output to ensure schema matches
                intent = result.get("intent", "rag")
                if intent not in ["small-talk", "rag", "sensitive"]:
                    intent = "rag"
                    
                rewritten_query = result.get("rewritten_query", query)
                suggested_answer = result.get("suggested_answer")
                
                # Expansion is now handled locally to save LLM tokens
                expanded = [rewritten_query]
                return {
                    "rewritten_query": rewritten_query,
                    "intent": intent,
                    "expanded_queries": expanded,
                    "suggested_answer": suggested_answer,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens
                    },
                    "fast_path": False
                }
            except Exception as e:
                log_warn("NLU", f"Unified NLU LLM Call failed: {e}. Falling back to Rule-based.")
        
        # Rule-based offline fallback if LLM is unavailable or crashes
        # 1. Simple heuristic fallback: intent classification
        intent = "rag"
        # Greetings check
        if any(w in query_lower for w in ["chào", "hi", "hello", "cảm ơn", "cảm ơn bạn", "tạm biệt", "bye"]):
            intent = "small-talk"
            
        # 2. Query rewrite fallback (just return original query since we have no LLM)
        rewritten_query = query
        
        # 3. Expansion fallback (use rule-based expansion or return list of rewritten)
        expanded = [rewritten_query]
        
        return {
            "rewritten_query": rewritten_query,
            "intent": intent,
            "expanded_queries": expanded,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            "fast_path": True,
            "fast_path_reason": "rule_based_fallback"
        }

if __name__ == "__main__":
    classifier = XanhSMClassifier()
    print("Unified NLU Test:", classifier.unified_nlu("Tôi gặp tai nạn nghiêm trọng trong chuyến xe"))
