from __future__ import annotations

import json
import re
from typing import Any

from app.food_recommendation.payloads import display_rating, format_food_answer
from app.core.config import settings as config
from app.core.llm import get_llm_client
from app.core.logger import log_warn
from app.prompts import FOOD_RECOMMENDER_ANSWER_SYSTEM_PROMPT


def stream_food_answer_with_llm(
    items: list[Any],
    query: str,
    slots: Any,
    food_context: dict[str, Any] | None = None,
):
    fallback_answer = format_food_answer(items, slots.category)
    fallback = {
        "answer": fallback_answer,
        "cards_title": None,
        "cards_subtitle": None,
        "item_notes": [],
        "llm_used": False,
        "error": None,
    }
    if not items:
        yield {"type": "done", "answer_meta": fallback}
        return
    if (not config.OPENAI_API_KEY and not config.GROQ_API_KEY) or config.EMBEDDING_PROVIDER == "mock" or ("YOUR_OPENAI_API_KEY" in config.OPENAI_API_KEY and not config.GROQ_API_KEY):
        yield {"type": "done", "answer_meta": fallback}
        return

    recommended_items = []
    for item in items[:4]: # CHỈ TRUYỀN 4 MÓN ĐẦU TIÊN VÀO LLM ĐỂ TRÁNH NHẦM LẪN VỚI MORE_ITEMS
        recommended_items.append({
            "item_id": item.item_id,
            "dish_name": item.name,
            "merchant_name": item.merchant_name,
            "address": item.address,
            "distance_km": item.distance_km,
            "eta_minutes": item.eta_minutes,
            "delivery_fee": item.delivery_fee,
            "price": item.final_price or item.price,
            "rating": display_rating(item.rating),
            "reason": item.reason,
            "score": round(float(item.score), 4),
        })

    user_payload = {
        "query": query,
        "food_slots": {
            "category": slots.category,
            "taste_tags": slots.taste_tags,
            "budget_min": slots.budget_min,
            "budget_max": slots.budget_max,
            "meal_time": slots.meal_time,
            "max_distance_km": slots.max_distance_km,
        },
        "user_context": food_context or {},
        "recommended_items": recommended_items,
    }
    if getattr(slots, "original_category", None):
        user_payload["food_slots"]["original_category_not_found"] = slots.original_category
    try:
        model_to_use = config.FOOD_ANSWER_MODEL
        client = get_llm_client(model_to_use)

        # Simplify prompt to just return text, not JSON
        prompt = FOOD_RECOMMENDER_ANSWER_SYSTEM_PROMPT.replace('Trả về JSON có cấu trúc:', '').replace('```json', '')
        # Add instruction to only generate the conversational answer
        prompt += "\n\nCHỈ TRẢ VỀ CÂU TRẢ LỜI GIAO TIẾP VỚI NGƯỜI DÙNG (không kèm JSON, không kèm metadata)."
        if getattr(slots, "original_category", None):
            prompt += f"\nCHÚ Ý QUAN TRỌNG: Quanh khu vực này KHÔNG CÓ món '{slots.original_category}' mà user yêu cầu. Hãy xin lỗi nhẹ nhàng và giải thích rằng bạn đã gợi ý các quán ăn khác (dưới đây) được đánh giá cao quanh khu vực để thay thế."

        response = client.chat.completions.create(
            model=model_to_use,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            temperature=0.3,
            max_tokens=400,
            stream=True
        )
        
        final_answer = ""
        try:
            for chunk in response:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    final_answer += text
                    yield {"type": "chunk", "text": text}
        except Exception as stream_error:
            log_warn("FOOD", f"Streaming generation interrupted: {stream_error}")
            if final_answer:
                error_notice = "\n\n*(Hệ thống bị gián đoạn kết nối, câu trả lời có thể chưa hoàn chỉnh)*"
                final_answer += error_notice
                yield {"type": "chunk", "text": error_notice}
            else:
                raise stream_error

        answer_meta = {
            "answer": final_answer.strip() or fallback_answer,
            "cards_title": None,
            "cards_subtitle": None,
            "item_notes": [],
            "llm_used": True,
            "error": None,
        }
        yield {"type": "done", "answer_meta": answer_meta}

    except Exception as exc:
        log_warn("FOOD", f"Error generating food answer: {exc}")
        fallback["error"] = str(exc)
        yield {"type": "done", "answer_meta": fallback}
