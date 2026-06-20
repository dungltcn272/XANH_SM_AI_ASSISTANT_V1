import json
import re
import unicodedata
from typing import Dict, Any, List
from app.core.config import settings as config
from app.core.llm import get_llm_client, has_api_key_for_model, select_model_for_multimodal
from app.prompts import UNIFIED_NLU_PROMPT
from app.core.logger import log_warn, log_info
from app.memory.context_builder import ContextBuilder

class XanhSMClassifier:
    """
    Unified Intent Classifier & Query Rewriter & Query Expander Gateway.
    """
    
    def __init__(self):
        self.fast_model = "gpt-4o-mini"

    def _memory_normalize(self, value: str | None) -> str:
        text = value or ""
        normalized = unicodedata.normalize("NFD", text)
        without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return without_marks.replace("đ", "d").replace("Đ", "D").casefold()

    def is_memory_related_query(self, query: str) -> bool:
        text = self._memory_normalize(query)
        patterns = [
            r"\b(toi|minh|em)\s+ten\s+la\b",
            r"\bten\s+(cua\s+)?(toi|minh)\b",
            r"\b(goi|keu)\s+(toi|minh)\s+la\b",
            r"\b(hay\s+)?(nho|ghi nho|luu)\b",
            r"\b(ban|em)\s+(co\s+)?nho\b",
            r"\b(toi|minh)\s+(thuong|hay)\b",
            r"\b(moi|hang)\s+(trua|sang|toi|ngay|tuan)\b",
        ]
        return any(re.search(pattern, text) for pattern in patterns)

    def _is_memory_write_only_query(self, query: str) -> bool:
        if self._is_memory_recall_query(query):
            return False
        text = self._memory_normalize(query)
        has_memory_signal = bool(re.search(r"\b(hay\s+)?(nho|ghi nho|luu)\b|\b(toi|minh)\s+(ten\s+la|thuong|hay)\b", text))
        has_action_request = bool(re.search(r"\b(goi y|tim|kiem|dat ngay|recommend|an gi|quan nao)\b", text))
        return has_memory_signal and not has_action_request

    def _is_memory_recall_query(self, query: str) -> bool:
        text = self._memory_normalize(query)
        return bool(re.search(r"\b(ban|em)\s+(co\s+)?nho\b|\bnho\s+(toi|minh)\b|\btoi\s+thuong\s+.*gi\b|\btoi\s+ten\s+gi\b", text))

    def _local_memory_candidates(self, query: str) -> list[dict[str, Any]]:
        text = query or ""
        if self._is_memory_recall_query(text):
            return []
        candidates: list[dict[str, Any]] = []

        normalized = self._memory_normalize(text)
        name_match = re.search(
            r"(?:tôi\s+tên\s+là|mình\s+tên\s+là|tên\s+tôi\s+là|gọi\s+tôi\s+là|kêu\s+tôi\s+là)\s+([^,.!?\n]{1,80})",
            text,
            flags=re.IGNORECASE,
        )
        if not name_match:
            name_match = re.search(
                r"(?:toi\s+ten\s+la|minh\s+ten\s+la|ten\s+toi\s+la|goi\s+toi\s+la|keu\s+toi\s+la)\s+([^,.!?\n]{1,80})",
                normalized,
                flags=re.IGNORECASE,
            )
        if name_match:
            display_name = name_match.group(1).strip()
            if display_name.islower():
                display_name = display_name.title()
            candidates.append({
                "scope": "general",
                "memory_type": "fact",
                "content": f"Người dùng muốn được gọi là {display_name}.",
                "confidence": 0.92,
                "metadata": {
                    "profile_field": "display_name",
                    "display_name": display_name,
                    "source": "local_memory_extractor",
                },
            })

        behavior_match = re.search(
            r"(?:tôi|mình)\s+(?:thường|hay)\s+([^.!?\n]{3,160})",
            text,
            flags=re.IGNORECASE,
        )
        if not behavior_match:
            behavior_match = re.search(
                r"(?:toi|minh)\s+(?:thuong|hay)\s+([^.!?\n]{3,160})",
                normalized,
                flags=re.IGNORECASE,
            )
        if behavior_match:
            behavior = behavior_match.group(1).strip(" ,.")
            behavior = re.split(r"\s*,?\s*(?:hay\s+)?(?:nho|ghi nho|luu)\b", behavior, maxsplit=1, flags=re.IGNORECASE)[0].strip(" ,.")
            if not behavior or re.search(r"\b(gi|khong)\b", self._memory_normalize(behavior)):
                behavior = ""
        if behavior_match and behavior:
            behavior_norm = self._memory_normalize(behavior)
            candidates.append({
                "scope": "food" if re.search(r"an|uong|dat|tra|com|pho|bun|quan|mon", behavior_norm, flags=re.IGNORECASE) else "general",
                "memory_type": "behavior",
                "content": f"Người dùng thường {behavior}.",
                "confidence": 0.86,
                "metadata": {"source": "local_memory_extractor"},
            })

        preference_match = re.search(
            r"(?:tôi|mình)\s+(?:thích|ưa)\s+([^.!?\n]{2,120})",
            text,
            flags=re.IGNORECASE,
        )
        if not preference_match:
            preference_match = re.search(
                r"(?:toi|minh)\s+(?:thich|ua)\s+([^.!?\n]{2,120})",
                normalized,
                flags=re.IGNORECASE,
            )
        if preference_match:
            preference = preference_match.group(1).strip(" ,.")
            preference_norm = self._memory_normalize(preference)
            candidates.append({
                "scope": "food" if re.search(r"an|uong|tra|com|pho|bun|mon", preference_norm, flags=re.IGNORECASE) else "general",
                "memory_type": "preference",
                "content": f"Người dùng thích {preference}.",
                "confidence": 0.84,
                "metadata": {"source": "local_memory_extractor"},
            })

        return candidates

    def _memory_recall_answer(self, assistant_context: Dict[str, Any] | None) -> str | None:
        context = assistant_context or {}
        profile = context.get("profile") or {}
        memories = context.get("relevant_memories") or []
        lines = []
        seen = set()
        display_name = profile.get("display_name")
        if display_name:
            line = f"anh/chị muốn được gọi là {display_name}"
            lines.append(line)
            seen.add(self._memory_normalize(line))
        for section in ("preferences", "behaviors", "facts", "constraints", "goals"):
            for item in profile.get(section) or []:
                content = item.get("content") if isinstance(item, dict) else None
                key = self._memory_normalize(content)
                if content and key not in seen and not (
                    display_name and section == "facts" and self._memory_normalize(display_name) in key
                ):
                    lines.append(content)
                    seen.add(key)
                if len(lines) >= 4:
                    break
            if len(lines) >= 4:
                break
        for memory in memories:
            content = memory.get("content") if isinstance(memory, dict) else None
            key = self._memory_normalize(content)
            if content and key not in seen and not (
                display_name and self._memory_normalize(display_name) in key
            ):
                lines.append(content)
                seen.add(key)
            if len(lines) >= 4:
                break
        if not lines:
            return "Dạ, hiện em chưa có thông tin đã lưu rõ ràng về phần này của anh/chị."
        return "Dạ, em đang ghi nhận: " + "; ".join(lines[:4]) + "."

    def _merge_memory_candidates(
        self,
        llm_candidates: list[dict[str, Any]],
        local_candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen = set()
        for candidate in [*(llm_candidates or []), *(local_candidates or [])]:
            if not isinstance(candidate, dict):
                continue
            key = (
                str(candidate.get("memory_type") or candidate.get("type") or ""),
                self._memory_normalize(str(candidate.get("content") or "")).strip(),
            )
            if not key[1] or key in seen:
                continue
            seen.add(key)
            merged.append(candidate)
        return merged

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

        # Decide which models to try (preferred NLU model first, failover to gpt-4o-mini)
        models_to_try = [model_to_use]
        if "gpt-4o-mini" not in models_to_try:
            models_to_try.append("gpt-4o-mini")

        result_payload = None
        for m in models_to_try:
            if not has_api_key_for_model(m):
                continue
            if config.EMBEDDING_PROVIDER == "mock":
                continue
            try:
                client = get_llm_client(m)
                
                messages = ContextBuilder.build_nlu_messages(
                    system_prompt=UNIFIED_NLU_PROMPT,
                    query=query,
                    chat_history=chat_history or [],
                    food_context=food_context,
                    assistant_context=assistant_context,
                    image_base64=image_base64 if include_image else None
                )

                response = client.chat.completions.create(
                    model=m,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=1000 if include_image else 650,
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
                
                # Expansion is now handled locally to save LLM tokens
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
                        "completion_tokens": response.usage.completion_tokens
                    },
                    "fast_path": False,
                    "nlu_model_used": m
                }
                break  # Success
            except Exception as e:
                log_warn("NLU", f"Unified NLU LLM Call failed for model {m}: {e}.")

        if result_payload is not None:
            return result_payload

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
