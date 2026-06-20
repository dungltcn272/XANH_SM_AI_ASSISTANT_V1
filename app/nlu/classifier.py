import json
import re
from typing import Any, Dict, List

from app.core.config import settings as config
from app.core.llm import get_llm_client, has_api_key_for_model, select_model_for_multimodal
from app.core.logger import log_warn
from app.memory.context_builder import ContextBuilder
from app.nlu.memory_extractor import MemorySignalExtractor
from app.prompts import UNIFIED_NLU_PROMPT


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
        1. Context-aware rewrite.
        2. Intent classification.
        3. Local memory signal correction.
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
                "memory_candidates": [],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "fast_path": True,
                "fast_path_reason": "safety_rule",
            }

        greeting_check = gateway.is_greeting_or_thanks(query)

        models_to_try = [model_to_use]
        if "gpt-4o-mini" not in models_to_try:
            models_to_try.append("gpt-4o-mini")

        result_payload = None
        for model_name in models_to_try:
            if not has_api_key_for_model(model_name):
                continue
            if config.EMBEDDING_PROVIDER == "mock":
                continue
            try:
                client = get_llm_client(model_name)

                messages = ContextBuilder.build_nlu_messages(
                    system_prompt=UNIFIED_NLU_PROMPT,
                    query=query,
                    chat_history=chat_history or [],
                    food_context=food_context,
                    assistant_context=assistant_context,
                    image_base64=image_base64 if include_image else None,
                )

                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=1000 if include_image else 650,
                    response_format={"type": "json_object"},
                )
                res_content = response.choices[0].message.content.strip()
                res_content = re.sub(r"```json|```", "", res_content).strip()
                result = json.loads(res_content)

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
                    "user_context": user_context,
                    "missing_fields": missing_fields,
                    "ui_form": ui_form,
                    "memory_candidates": memory_candidates,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                    },
                    "fast_path": False,
                    "nlu_model_used": model_name,
                }
                break
            except Exception as exc:
                log_warn("NLU", f"Unified NLU LLM Call failed for model {model_name}: {exc}.")

        if result_payload is not None:
            return result_payload

        intent = "rag"
        if greeting_check["type"] != "none":
            intent = "small-talk"

        rewritten_query = query
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
            "fast_path_reason": "rule_based_fallback",
        }


if __name__ == "__main__":
    classifier = XanhSMClassifier()
    classifier.unified_nlu("Tôi gặp tai nạn nghiêm trọng trong chuyến xe")
