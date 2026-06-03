import json
import re
from typing import Dict, Any, List, Tuple, Optional
from openai import OpenAI
from app.core.config import settings as config
from app.rag.prompt import UNIFIED_NLU_PROMPT
from app.core.logger import log_warn

class XanhSMClassifier:
    """
    Unified Intent Classifier & Query Rewriter & Query Expander Gateway.
    """
    
    def __init__(self):
        pass

    def unified_nlu(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
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
                "intent": "small-talk", # Redirect to a safe template answer
                "expanded_queries": [query],
                "safety_blocked": True,
                "safety_reason": safety_res["reason"]
            }

        # Rule-based Small-talk fast check (exact matches or very short phrases)
        greeting_check = gateway.is_greeting_or_thanks(query)
        if greeting_check["type"] != "none":
            return {
                "rewritten_query": query,
                "intent": "small-talk",
                "expanded_queries": [query]
            }

        # If LLM is available, use it for NLU
        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                history_str = ""
                if chat_history:
                    # Keep only last 3 turns to keep context compact and focus NLU
                    for turn in chat_history[-3:]:
                        role_tag = "User" if turn.get("role") == "user" else "Assistant"
                        history_str += f"{role_tag}: {turn.get('content')}\n"

                client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=15.0)
                user_prompt = f"Lịch sử hội thoại:\n{history_str}\nCâu hỏi mới nhất: '{query}'\nJSON kết quả:"
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": UNIFIED_NLU_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                res_content = response.choices[0].message.content.strip()
                result = json.loads(res_content)
                
                # Normalize output to ensure schema matches
                intent = result.get("intent", "rag")
                if intent not in ["small-talk", "rag"]:
                    intent = "rag"
                    
                rewritten_query = result.get("rewritten_query", query)
                expanded = result.get("expanded_queries", [])
                if not isinstance(expanded, list):
                    expanded = [rewritten_query]
                
                # Ensure the rewritten query is in the expansion list
                if rewritten_query not in expanded:
                    expanded = [rewritten_query] + expanded
                    
                return {
                    "rewritten_query": rewritten_query,
                    "intent": intent,
                    "expanded_queries": expanded,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens
                    }
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
        from app.retrieval.multi_query import XanhSMQueryExpansion
        expander = XanhSMQueryExpansion()
        expanded = expander.expand_query_rule_based(rewritten_query)
        
        return {
            "rewritten_query": rewritten_query,
            "intent": intent,
            "expanded_queries": expanded,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0}
        }

if __name__ == "__main__":
    classifier = XanhSMClassifier()
    print("Unified NLU Test:", classifier.unified_nlu("Tôi gặp tai nạn nghiêm trọng trong chuyến xe"))
