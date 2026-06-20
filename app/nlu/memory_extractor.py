import re
import unicodedata
from typing import Any


class MemorySignalExtractor:
    """Local memory heuristics used as a safety net around LLM NLU output."""

    def normalize(self, value: str | None) -> str:
        text = value or ""
        normalized = unicodedata.normalize("NFD", text)
        without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return without_marks.replace("đ", "d").replace("Đ", "D").casefold()

    def is_memory_related_query(self, query: str) -> bool:
        text = self.normalize(query)
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

    def is_memory_write_only_query(self, query: str) -> bool:
        if self.is_memory_recall_query(query):
            return False
        text = self.normalize(query)
        has_memory_signal = bool(
            re.search(r"\b(hay\s+)?(nho|ghi nho|luu)\b|\b(toi|minh)\s+(ten\s+la|thuong|hay)\b", text)
        )
        has_action_request = bool(re.search(r"\b(goi y|tim|kiem|dat ngay|recommend|an gi|quan nao)\b", text))
        return has_memory_signal and not has_action_request

    def is_memory_recall_query(self, query: str) -> bool:
        text = self.normalize(query)
        return bool(
            re.search(r"\b(ban|em)\s+(co\s+)?nho\b|\bnho\s+(toi|minh)\b|\btoi\s+thuong\s+.*gi\b|\btoi\s+ten\s+gi\b", text)
        )

    def local_memory_candidates(self, query: str) -> list[dict[str, Any]]:
        text = query or ""
        if self.is_memory_recall_query(text):
            return []
        candidates: list[dict[str, Any]] = []

        normalized = self.normalize(text)
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
        behavior = ""
        if behavior_match:
            behavior = behavior_match.group(1).strip(" ,.")
            behavior = re.split(
                r"\s*,?\s*(?:hay\s+)?(?:nho|ghi nho|luu)\b",
                behavior,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0].strip(" ,.")
            if not behavior or re.search(r"\b(gi|khong)\b", self.normalize(behavior)):
                behavior = ""
        if behavior_match and behavior:
            behavior_norm = self.normalize(behavior)
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
            preference_norm = self.normalize(preference)
            candidates.append({
                "scope": "food" if re.search(r"an|uong|tra|com|pho|bun|mon", preference_norm, flags=re.IGNORECASE) else "general",
                "memory_type": "preference",
                "content": f"Người dùng thích {preference}.",
                "confidence": 0.84,
                "metadata": {"source": "local_memory_extractor"},
            })

        return candidates

    def recall_answer(self, assistant_context: dict[str, Any] | None) -> str | None:
        context = assistant_context or {}
        profile = context.get("profile") or {}
        memories = context.get("relevant_memories") or []
        lines = []
        seen = set()
        display_name = profile.get("display_name")
        if display_name:
            line = f"anh/chị muốn được gọi là {display_name}"
            lines.append(line)
            seen.add(self.normalize(line))
        for section in ("preferences", "behaviors", "facts", "constraints", "goals"):
            for item in profile.get(section) or []:
                content = item.get("content") if isinstance(item, dict) else None
                key = self.normalize(content)
                if content and key not in seen and not (
                    display_name and section == "facts" and self.normalize(display_name) in key
                ):
                    lines.append(content)
                    seen.add(key)
                if len(lines) >= 4:
                    break
            if len(lines) >= 4:
                break
        for memory in memories:
            content = memory.get("content") if isinstance(memory, dict) else None
            key = self.normalize(content)
            if content and key not in seen and not (
                display_name and self.normalize(display_name) in key
            ):
                lines.append(content)
                seen.add(key)
            if len(lines) >= 4:
                break
        if not lines:
            return "Dạ, hiện em chưa có thông tin đã lưu rõ ràng về phần này của anh/chị."
        return "Dạ, em đang ghi nhận: " + "; ".join(lines[:4]) + "."

    def merge_memory_candidates(
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
                self.normalize(str(candidate.get("content") or "")).strip(),
            )
            if not key[1] or key in seen:
                continue
            seen.add(key)
            merged.append(candidate)
        return merged
