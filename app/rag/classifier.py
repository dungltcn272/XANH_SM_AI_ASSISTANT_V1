import json
import re
from typing import Dict, Any, List
from app.core.config import settings as config
from app.core.llm import get_llm_client, has_api_key_for_model, select_model_for_multimodal
from app.prompts import UNIFIED_NLU_PROMPT
from app.core.logger import log_warn
from app.memory.context_builder import ContextBuilder

class XanhSMClassifier:
    """
    Unified Intent Classifier & Query Rewriter & Query Expander Gateway.
    """
    
    def __init__(self):
        self.fast_model = "gpt-4o-mini"

    def unified_nlu(
        self,
        query: str,
        chat_history: List[Dict[str, str]] = None,
        image_base64: str = None,
        food_context: Dict[str, Any] | None = None,
        assistant_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Unified 3-in-1 NLU Analyzer:
        1. Context-aware rewrite
        2. Intent classification (rag, small-talk)
        3. Query expansion
        """
        model_to_use = config.NLU_MODEL
        include_image = False
        if image_base64:
            multimodal_model = select_model_for_multimodal(config.NLU_MODEL, config.VLM_MODEL)
            if multimodal_model:
                model_to_use = multimodal_model
                include_image = True

        llm_available = (
            has_api_key_for_model(model_to_use)
            and config.EMBEDDING_PROVIDER != "mock"
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
                "memory_candidates": [],
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
                "memory_candidates": [],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "fast_path": True,
                "fast_path_reason": "small_talk_rule"
            }

        # If LLM is available, use it for NLU
        if llm_available:
            try:
                client = get_llm_client(model_to_use)
                
                messages = ContextBuilder.build_nlu_messages(
                    system_prompt=UNIFIED_NLU_PROMPT,
                    query=query,
                    chat_history=chat_history or [],
                    food_context=food_context,
                    assistant_context=assistant_context,
                    image_base64=image_base64 if include_image else None
                )

                response = client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=650,
                    response_format={"type": "json_object"}
                )
                res_content = response.choices[0].message.content.strip()
                res_content = re.sub(r"```json|```", "", res_content).strip()
                result = json.loads(res_content)
                
                # Normalize output to ensure schema matches
                intent = result.get("intent", "rag")
                if intent == "food-recommend":
                    intent = "food_recommendation"
                if intent in ["miss-info", "missing-info", "missinginfo"]:
                    intent = "missing_info"
                if intent not in ["small-talk", "rag", "sensitive", "missing_info", "food_recommendation"]:
                    intent = "rag"
                    
                rewritten_query = result.get("rewritten_query", query)
                suggested_answer = result.get("suggested_answer")
                food_slots = result.get("food_slots")
                user_context = result.get("user_context")
                missing_fields = result.get("missing_fields") or []
                ui_form = result.get("ui_form")
                memory_candidates = result.get("memory_candidates") or []
                if not isinstance(memory_candidates, list):
                    memory_candidates = []
                
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
                    "memory_candidates": memory_candidates,
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
            "memory_candidates": [],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            "fast_path": True,
            "fast_path_reason": "rule_based_fallback"
        }

if __name__ == "__main__":
    classifier = XanhSMClassifier()
    classifier.unified_nlu("Tôi gặp tai nạn nghiêm trọng trong chuyến xe")
