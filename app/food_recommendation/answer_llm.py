from __future__ import annotations

from typing import Any

from app.core.config import settings as config
from app.core.llm import get_llm_client
from app.core.logger import log_warn
from app.food_recommendation.payloads import display_rating, format_food_answer
from app.memory.context_builder import ContextBuilder
from app.prompts import FOOD_RECOMMENDER_ANSWER_SYSTEM_PROMPT


def stream_food_answer_with_llm(
    items: list[Any],
    query: str,
    slots: Any,
    food_context: dict[str, Any] | None = None,
    chat_history: list[dict[str, str]] | None = None,
    assistant_context: dict[str, Any] | None = None,
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

    # Only pass items that FE renders as primary cards. This keeps the LLM from
    # recommending hidden "more_items" and makes ::FOOD_CARD ids reliable.
    recommended_items = [
        {
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
        }
        for item in items[:4]
    ]
    try:
        model_to_use = config.FOOD_ANSWER_MODEL
        client = get_llm_client(model_to_use)

        messages = ContextBuilder.build_food_messages(
            system_prompt=FOOD_RECOMMENDER_ANSWER_SYSTEM_PROMPT,
            query=query,
            chat_history=chat_history or [],
            food_context=food_context,
            recommended_items=recommended_items,
            slots=slots,
            assistant_context=assistant_context,
        )

        response = client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            temperature=0.3,
            max_tokens=400,
            stream=True,
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
