import json
import re
from typing import Any, Dict, List
import concurrent.futures

from app.core.config import settings as config
from app.core.llm import get_llm_client, has_api_key_for_model, select_model_for_multimodal
from app.core.logger import log_warn
from app.memory.context_builder import ContextBuilder
from app.nlu.memory_extractor import MemorySignalExtractor
from app.prompts.system_prompts import (
    NLU_INTENT_REWRITE_PROMPT,
    NLU_FOOD_EXTRACTION_PROMPT,
    NLU_MEMORY_EXTRACTION_PROMPT
)


class XanhSMClassifier:
    """
    Unified NLU analyzer.

    Owns intent classification, query rewrite, food slot pass-through, and the
    final normalization of the LLM JSON result. Local memory heuristics live in
    MemorySignalExtractor so NLU routing and memory extraction can evolve
    independently.
    """

    def __init__(self):
        self.fast_model = "gpt-4o-mini"
        self.memory_extractor = MemorySignalExtractor()

    def _memory_normalize(self, value: str | None) -> str:
        return self.memory_extractor.normalize(value)

    def is_memory_related_query(self, query: str) -> bool:
        return self.memory_extractor.is_memory_related_query(query)

    def _is_memory_write_only_query(self, query: str) -> bool:
        return self.memory_extractor.is_memory_write_only_query(query)

    def _is_memory_recall_query(self, query: str) -> bool:
        return self.memory_extractor.is_memory_recall_query(query)

    def _local_memory_candidates(self, query: str) -> list[dict[str, Any]]:
        return self.memory_extractor.local_memory_candidates(query)

    def _memory_recall_answer(self, assistant_context: Dict[str, Any] | None) -> str | None:
        return self.memory_extractor.recall_answer(assistant_context)

    def _is_map_related_query(self, query: str) -> bool:
        text = self._memory_normalize(query)
        map_terms = [
            "ban do",
            "map",
            "heatmap",
            "tai xe dong",
            "dong tai xe",
            "xe quanh",
            "dong khach",
            "diem dong",
            "tac duong",
            "ket xe",
            "un tac",
            "duong tat",
            "duong nhanh",
            "traffic",
            "shortcut",
        ]
        return any(term in text for term in map_terms)

    def _local_map_slots(self, query: str, intent: str) -> dict[str, Any] | None:
        if intent != "map_intelligence":
            return None
        text = self._memory_normalize(query)
        layers = []
        if any(term in text for term in ["tai xe", "driver", "xe quanh", "dong xe"]):
            layers.append("drivers")
        if any(term in text for term in ["quan", "an", "food", "nha hang", "restaurant"]):
            layers.append("restaurants")
        if any(term in text for term in ["dong khach", "nhu cau", "diem dong", "hotspot"]):
            layers.append("demand")
        if any(term in text for term in ["tac", "ket", "traffic", "un"]):
            layers.append("traffic")
        if any(term in text for term in ["duong tat", "ne", "shortcut", "duong nhanh"]):
            layers.append("shortcuts")
        user_mode = "driver" if any(term in text for term in ["tai xe nen", "don khach", "chay xe"]) else "customer"
        coord_match = re.search(r"(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)", query or "")
        slots: dict[str, Any] = {"layers": layers or None, "user_mode": user_mode, "radius_km": 5.0}
        if coord_match:
            slots["lat"] = float(coord_match.group(1))
            slots["lng"] = float(coord_match.group(2))
        return slots

    def _merge_memory_candidates(
        self,
        llm_candidates: list[dict[str, Any]],
        local_candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return self.memory_extractor.merge_memory_candidates(llm_candidates, local_candidates)

    def unified_nlu(
        self,
        query: str,
        chat_history: List[Dict[str, str]] = None,
        image_base64: str = None,
        food_context: Dict[str, Any] | None = None,
        assistant_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Unified NLU analyzer:
        1. Context-aware rewrite & Intent classification (Call 1)
        2. Local memory signal correction & LLM memory extraction (Call 2 - Async)
        3. Food Slot extraction (Call 3 - Only if intent is food_recommendation)
        """
        model_to_use = config.NLU_MODEL
        include_image = False
        if image_base64:
            multimodal_model = select_model_for_multimodal(config.NLU_MODEL, config.VLM_MODEL)
            if multimodal_model:
                model_to_use = multimodal_model
                include_image = True

        from app.rag.core.gateway import XanhSMGateway

        gateway = XanhSMGateway()
        safety_res = gateway.safety_precheck(query)
        if not safety_res["safe"]:
            return {
                "rewritten_query": query,
                "intent": "sensitive",
                "expanded_queries": [query],
                "safety_blocked": True,
                "safety_reason": safety_res["reason"],
                "suggested_answer": None,
                "food_slots": None,
                "map_slots": None,
                "memory_candidates": [],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "fast_path": True,
                "fast_path_reason": "safety_rule",
            }

        greeting_check = gateway.is_greeting_or_thanks(query)

        models_to_try = [model_to_use]
        if "gpt-4o-mini" not in models_to_try:
            models_to_try.append("gpt-4o-mini")

        def _call_llm_json(system_prompt: str, max_tokens: int, target_model: str) -> dict:
            try:
                client = get_llm_client(target_model)
                messages = ContextBuilder.build_nlu_messages(
                    system_prompt=system_prompt,
                    query=query,
                    chat_history=chat_history or [],
                    food_context=food_context,
                    assistant_context=assistant_context,
                    image_base64=image_base64 if include_image else None,
                )
                kwargs = {
                    "model": target_model,
                    "messages": messages,
                    "temperature": 0.0,
                    "max_tokens": max_tokens,
                }
                
                # An toàn: Chỉ ép response_format JSON cho các model của OpenAI (hỗ trợ tốt chuẩn này).
                # Các model Open-source (Qwen, Llama...) qua OpenRouter có thể không hỗ trợ hoặc lỗi validate JSON.
                if "gpt" in target_model.lower():
                    kwargs["response_format"] = {"type": "json_object"}
                    
                response = client.chat.completions.create(**kwargs)
                res_content = response.choices[0].message.content or ""
                res_content = res_content.strip()
                
                # Robust JSON extraction
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", res_content, re.DOTALL)
                if match:
                    json_str = match.group(1)
                else:
                    start = res_content.find('{')
                    end = res_content.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        json_str = res_content[start:end+1]
                    else:
                        json_str = "{}" # Fallback if no JSON found
                
                return {
                    "result": json.loads(json_str),
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                    }
                }
            except Exception as exc:
                log_warn("NLU", f"Unified NLU LLM Call failed for model {target_model}: {exc}.")
                return {"result": {}, "usage": {"prompt_tokens": 0, "completion_tokens": 0}, "error": str(exc)}

        result_payload = None
        for model_name in models_to_try:
            if not has_api_key_for_model(model_name):
                continue
            if config.EMBEDDING_PROVIDER == "mock":
                continue
            
            # Using ThreadPoolExecutor to run Memory Extraction and Intent Classification concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_intent = executor.submit(_call_llm_json, NLU_INTENT_REWRITE_PROMPT, 650 if include_image else 300, model_name)
                future_memory = executor.submit(_call_llm_json, NLU_MEMORY_EXTRACTION_PROMPT, 500, model_name)
                
                intent_resp = future_intent.result()
                if "error" in intent_resp:
                    continue # Try next model if intent classification failed
                
                intent_data = intent_resp["result"]
                intent = intent_data.get("intent", "rag")
                if intent == "food-recommend":
                    intent = "food_recommendation"
                if intent in ["miss-info", "missing-info", "missinginfo"]:
                    intent = "missing_info"
                if intent in ["map", "map-intelligence", "map_intent", "geo_map"]:
                    intent = "map_intelligence"
                if intent not in ["small-talk", "rag", "sensitive", "missing_info", "food_recommendation", "map_intelligence"]:
                    intent = "rag"
                if intent == "rag" and self._is_map_related_query(query):
                    intent = "map_intelligence"

                rewritten_query = intent_data.get("rewritten_query", query)
                suggested_answer = intent_data.get("suggested_answer")
                
                # Fetch memory result
                memory_resp = future_memory.result()
                memory_data = memory_resp.get("result", {})
                memory_candidates = memory_data.get("memory_candidates") or []
                if not isinstance(memory_candidates, list):
                    memory_candidates = []
                
                # If intent is food, we do a sequential 3rd call for slots
                food_slots = None
                missing_fields = []
                ui_form = None
                food_usage = {"prompt_tokens": 0, "completion_tokens": 0}
                if intent == "food_recommendation":
                    food_resp = _call_llm_json(NLU_FOOD_EXTRACTION_PROMPT, 500, model_name)
                    food_data = food_resp.get("result", {})
                    food_slots = food_data.get("food_slots")
                    missing_fields = food_data.get("missing_fields") or []
                    ui_form = food_data.get("ui_form")
                    food_usage = food_resp.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})
                
                # Usage aggregation
                total_prompt_tokens = intent_resp["usage"]["prompt_tokens"] + memory_resp["usage"]["prompt_tokens"] + food_usage["prompt_tokens"]
                total_completion_tokens = intent_resp["usage"]["completion_tokens"] + memory_resp["usage"]["completion_tokens"] + food_usage["completion_tokens"]

                # Process local memory overrides
                memory_candidates = self._merge_memory_candidates(
                    memory_candidates,
                    self._local_memory_candidates(query),
                )
                if self._is_memory_write_only_query(query):
                    intent = "small-talk"
                    suggested_answer = suggested_answer or "Dạ, em đã ghi nhận thông tin này để hỗ trợ anh/chị tốt hơn."
                    food_slots = None
                    missing_fields = []
                    ui_form = None
                elif self._is_memory_recall_query(query):
                    intent = "small-talk"
                    suggested_answer = self._memory_recall_answer(assistant_context) or suggested_answer
                    food_slots = None
                    missing_fields = []
                    ui_form = None

                expanded = [rewritten_query]
                result_payload = {
                    "rewritten_query": rewritten_query,
                    "intent": intent,
                    "expanded_queries": expanded,
                    "suggested_answer": suggested_answer,
                    "food_slots": food_slots,
                    "map_slots": self._local_map_slots(query, intent),
                    "user_context": food_slots, # Keep compatible with old logic if needed
                    "missing_fields": missing_fields,
                    "ui_form": ui_form,
                    "memory_candidates": memory_candidates,
                    "usage": {
                        "prompt_tokens": total_prompt_tokens,
                        "completion_tokens": total_completion_tokens,
                    },
                    "fast_path": False,
                    "nlu_model_used": model_name,
                }
                break

        if result_payload is not None:
            return result_payload

        intent = "rag"
        if greeting_check["type"] != "none":
            intent = "small-talk"
        elif self._is_map_related_query(query):
            intent = "map_intelligence"

        rewritten_query = query
        expanded = [rewritten_query]

        return {
            "rewritten_query": rewritten_query,
            "intent": intent,
            "expanded_queries": expanded,
            "suggested_answer": None,
            "food_slots": None,
            "map_slots": self._local_map_slots(query, intent),
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
            "fast_path_reason": "rule_based_fallback",
        }


if __name__ == "__main__":
    classifier = XanhSMClassifier()
    classifier.unified_nlu("Tôi gặp tai nạn nghiêm trọng trong chuyến xe")
