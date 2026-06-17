import json
import re
from typing import Dict, Any, List
from openai import OpenAI
from app.core.config import settings as config
from app.prompts import UNIFIED_NLU_PROMPT
from app.core.logger import log_warn

class XanhSMClassifier:
    """
    Unified Intent Classifier & Query Rewriter & Query Expander Gateway.
    """
    
    def __init__(self):
        pass

    def unified_nlu(
        self,
        query: str,
        chat_history: List[Dict[str, str]] = None,
        image_base64: str = None,
        food_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Unified 3-in-1 NLU Analyzer:
        1. Context-aware rewrite
        2. Intent classification (rag, small-talk)
        3. Query expansion
        """
        llm_available = (
            config.OPENAI_API_KEY
            and config.EMBEDDING_PROVIDER != "mock"
            and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY
        )
        
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

        # Rule-based fallbacks are only used when the NLU LLM is unavailable.
        greeting_check = gateway.is_greeting_or_thanks(query)
        if not llm_available and greeting_check["type"] != "none":
            return {
                "rewritten_query": query,
                "intent": "small-talk",
                "expanded_queries": [query],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "fast_path": True,
                "fast_path_reason": "small_talk_rule"
            }

        # If LLM is available, use it for NLU
        if llm_available:
            try:
                history_str = ""
                if chat_history:
                    # Keep only last 3 turns to keep context compact and focus NLU
                    for turn in chat_history[-3:]:
                        role_tag = "User" if turn.get("role") == "user" else "Assistant"
                        history_str += f"{role_tag}: {turn.get('content')}\n"

                client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.OPENAI_TIMEOUT_SECONDS)
                food_context_str = json.dumps(food_context or {}, ensure_ascii=False, indent=2)
                user_prompt = (
                    f"Lịch sử hội thoại:\n{history_str}\n"
                    f"Food user context từ DB (field chưa biết là null/[]):\n{food_context_str}\n"
                    f"Câu hỏi mới nhất: '{query}'\nJSON kết quả:"
                )
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
                    max_tokens=650,
                    response_format={"type": "json_object"}
                )
                res_content = response.choices[0].message.content.strip()
                # Cleanup potential markdown blocks
                res_content = re.sub(r"```json|```", "", res_content).strip()
                result = json.loads(res_content)
                
                # Normalize output to ensure schema matches
                intent = result.get("intent", "rag")
                if intent == "food-recommend":
                    intent = "food_recommendation"
                if intent not in ["small-talk", "rag", "sensitive", "food_recommendation"]:
                    intent = "rag"
                    
                rewritten_query = result.get("rewritten_query", query)
                suggested_answer = result.get("suggested_answer")
                food_slots = result.get("food_slots")
                user_context = result.get("user_context")
                missing_fields = result.get("missing_fields") or []
                ui_form = result.get("ui_form")
                
                # Expansion is now handled locally to save LLM tokens
                expanded = [rewritten_query]
                return {
                    "rewritten_query": rewritten_query,
                    "intent": intent,
                    "expanded_queries": expanded,
                    "suggested_answer": suggested_answer,
                    "food_slots": food_slots,
                    "user_context": user_context,
                    "missing_fields": missing_fields,
                    "ui_form": ui_form,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens
                    },
                    "fast_path": False
                }
            except Exception as e:
                log_warn("NLU", f"Unified NLU LLM Call failed: {e}. Falling back to Rule-based.")
        
        # Rule-based offline fallback if LLM is unavailable or crashes
        # 1. Offline fallback: do not infer food/RAG intent by keyword here.
        # Gateway-only greeting fallback is kept because gateway owns that rule layer.
        intent = "rag"
        if greeting_check["type"] != "none":
            intent = "small-talk"
            
        # 2. Query rewrite fallback (just return original query since we have no LLM)
        rewritten_query = query
        
        # 3. Expansion fallback (use rule-based expansion or return list of rewritten)
        expanded = [rewritten_query]
        
        return {
            "rewritten_query": rewritten_query,
            "intent": intent,
            "expanded_queries": expanded,
            "suggested_answer": None,
            "food_slots": None,
            "user_context": food_context if intent == "food_recommendation" else None,
            "missing_fields": ["location"] if intent == "food_recommendation" else [],
            "ui_form": {
                "type": "food_missing_info",
                "required_fields": ["location"],
                "optional_fields": ["budget", "taste", "liked_foods", "disliked_foods"],
                "map_required": True,
            } if intent == "food_recommendation" else None,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            "fast_path": True,
            "fast_path_reason": "rule_based_fallback"
        }

if __name__ == "__main__":
    classifier = XanhSMClassifier()
    print("Unified NLU Test:", classifier.unified_nlu("Tôi gặp tai nạn nghiêm trọng trong chuyến xe"))
