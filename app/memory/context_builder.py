from __future__ import annotations

import json
from typing import Any


class ContextBuilder:
    """Builds prompt messages from static instructions and dynamic context."""

    @staticmethod
    def _format_history(
        chat_history: list[dict[str, str]] | None,
        *,
        limit: int = 6,
        max_chars_per_turn: int = 420,
    ) -> str:
        if not chat_history:
            return "Không có lịch sử hội thoại gần đây."

        lines: list[str] = []
        for turn in chat_history[-limit:]:
            role = turn.get("role") or ""
            role_label = "User" if role == "user" else "Assistant"
            content = (turn.get("content") or "").strip()
            if len(content) > max_chars_per_turn:
                content = content[:max_chars_per_turn].rstrip() + "... [truncated]"
            if content:
                lines.append(f"{role_label}: {content}")
        return "\n".join(lines) if lines else "Không có lịch sử hội thoại gần đây."

    @staticmethod
    def _format_nlu_history(chat_history: list[dict[str, str]] | None) -> str:
        """Give NLU enough dialogue state to resolve short follow-up queries."""
        return ContextBuilder._format_history(
            chat_history,
            limit=10,
            max_chars_per_turn=1400,
        )

    @staticmethod
    def _json_block(value: Any) -> str:
        if value in (None, "", [], {}):
            return "{}"
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)

    @staticmethod
    def _slot_payload(slots: Any) -> dict[str, Any]:
        if slots is None:
            return {}
        return {
            "category": getattr(slots, "category", None),
            "taste_tags": getattr(slots, "taste_tags", []),
            "budget_min": getattr(slots, "budget_min", None),
            "budget_max": getattr(slots, "budget_max", None),
            "meal_time": getattr(slots, "meal_time", None),
            "address_text": getattr(slots, "address_text", None),
            "lat": getattr(slots, "lat", None),
            "lng": getattr(slots, "lng", None),
            "max_distance_km": getattr(slots, "max_distance_km", None),
            "original_category_not_found": getattr(slots, "original_category", None),
        }

    @staticmethod
    def build_nlu_messages(
        system_prompt: str,
        query: str,
        chat_history: list[dict[str, str]] | None,
        food_context: dict[str, Any] | None,
        assistant_context: dict[str, Any] | None = None,
        image_base64: str | None = None,
    ) -> list[dict[str, Any]]:
        user_prompt = (
            "ASSISTANT_MEMORY_CONTEXT:\n"
            f"{ContextBuilder._json_block(assistant_context)}\n\n"
            "LONG_TERM_USER_MEMORY:\n"
            f"{ContextBuilder._json_block(food_context)}\n\n"
            "WORKING_MEMORY:\n"
            f"{ContextBuilder._format_nlu_history(chat_history)}\n\n"
            "CURRENT_QUERY:\n"
            f"{query}\n\n"
            f"IMAGE_ATTACHED: {'yes' if image_base64 else 'no'}\n\n"
            "Yêu cầu: phân tích input trên và trả về đúng JSON schema trong system prompt. "
            "Nếu CURRENT_QUERY là câu nối tiếp ngắn, lựa chọn một option/card/mục đã được Assistant nêu, "
            "hoặc yêu cầu kiểu 'cái đó', 'cái đầu', 'mục này', 'so sánh hai cái này', hãy dùng WORKING_MEMORY "
            "để viết lại thành câu hỏi độc lập trước khi phân loại intent. "
            "Nếu IMAGE_ATTACHED=yes, hãy đọc kỹ nội dung ảnh và đưa các chữ, nút, bước, lỗi, số liệu hoặc trạng thái "
            "quan trọng vào rewritten_query; không được rewrite chung chung như 'xác thực thông tin trong ảnh'."
        )

        if image_base64:
            user_content: str | list[dict[str, Any]] = [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": "high",
                    },
                },
            ]
        else:
            user_content = user_prompt

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    @staticmethod
    def build_rag_messages(
        system_prompt: str,
        query: str,
        chat_history: list[dict[str, str]] | None,
        compressed_context: str,
        food_context: dict[str, Any] | None = None,
        assistant_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        user_prompt = (
            "ASSISTANT_MEMORY_CONTEXT:\n"
            f"{ContextBuilder._json_block(assistant_context)}\n\n"
            "USER_PROFILE:\n"
            f"{ContextBuilder._json_block(food_context)}\n\n"
            "WORKING_MEMORY:\n"
            f"{ContextBuilder._format_history(chat_history, limit=6)}\n\n"
            "RAG_CONTEXT:\n"
            f"{compressed_context or 'Không có dữ liệu liên quan.'}\n\n"
            "CURRENT_QUERY:\n"
            f"{query}\n\n"
            "Yêu cầu: trả lời trực tiếp cho người dùng theo system prompt."
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    @staticmethod
    def build_food_messages(
        system_prompt: str,
        query: str,
        chat_history: list[dict[str, str]] | None,
        food_context: dict[str, Any] | None,
        recommended_items: list[dict[str, Any]],
        slots: Any,
        assistant_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        food_request = {
            "query": query,
            "slots": ContextBuilder._slot_payload(slots),
        }

        user_prompt = (
            "ASSISTANT_MEMORY_CONTEXT:\n"
            f"{ContextBuilder._json_block(assistant_context)}\n\n"
            "USER_PROFILE:\n"
            f"{ContextBuilder._json_block(food_context)}\n\n"
            "WORKING_MEMORY:\n"
            f"{ContextBuilder._format_history(chat_history, limit=6)}\n\n"
            "FOOD_REQUEST:\n"
            f"{ContextBuilder._json_block(food_request)}\n\n"
            "RECOMMENDED_ITEMS:\n"
            f"{ContextBuilder._json_block(recommended_items)}\n\n"
            "Yêu cầu: stream câu trả lời tự nhiên. Khi muốn hiển thị card món/quán, "
            "chèn marker `[[FOOD_CARD {...}]]` theo đúng schema trong system prompt."
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
