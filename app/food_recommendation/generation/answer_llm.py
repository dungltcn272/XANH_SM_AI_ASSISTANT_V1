from __future__ import annotations

from typing import Any

from app.core.config import settings as config
from app.core.llm import get_llm_client
from app.core.logger import log_warn
from app.food_recommendation.generation.payloads import (
    display_rating,
    distance_text,
    format_food_answer,
    format_vnd,
)
from app.memory.context_builder import ContextBuilder
from app.prompts import FOOD_RECOMMENDER_ANSWER_SYSTEM_PROMPT

CARD_START = "[[FOOD_CARD"


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
        "food_cards": None,
        "food_card_count": 0,
        "food_cards_source": "none",
        "llm_used": False,
        "error": None,
    }
    if not items:
        yield {"type": "done", "answer_meta": fallback}
        return
    if (
        (not config.OPENAI_API_KEY and not config.GROQ_API_KEY)
        or config.EMBEDDING_PROVIDER == "mock"
        or ("YOUR_OPENAI_API_KEY" in config.OPENAI_API_KEY and not config.GROQ_API_KEY)
    ):
        yield {"type": "done", "answer_meta": fallback}
        return

    recommended_items = [_candidate_payload(item, index) for index, item in enumerate(items[:4])]

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
            max_tokens=1800,
            stream=True,
        )

        final_answer = ""
        for chunk in response:
            text = chunk.choices[0].delta.content
            if not text:
                continue
            final_answer += text
            yield {"type": "chunk", "text": text}

        marker_count = final_answer.count(CARD_START)
        yield {
            "type": "done",
            "answer_meta": {
                "answer": final_answer.strip() or fallback_answer,
                "food_cards": None,
                "food_card_count": marker_count,
                "food_cards_source": "raw_llm_marker" if marker_count else "none",
                "llm_used": True,
                "error": None,
            },
        }

    except Exception as exc:
        log_warn("FOOD", f"Error generating food answer: {exc}")
        fallback["error"] = str(exc)
        yield {"type": "done", "answer_meta": fallback}


def _candidate_payload(item: Any, index: int) -> dict[str, Any]:
    price = item.final_price or item.price
    return {
        "item_id": item.item_id,
        "name": item.merchant_name or item.name,
        "dish_name": item.name,
        "merchant_name": item.merchant_name,
        "address": item.address,
        "image_url": item.image_url,
        "order_url": item.order_url,
        "distance_km": item.distance_km,
        "distance_text": distance_text(item.distance_km),
        "eta_minutes": item.eta_minutes,
        "eta_text": f"{item.eta_minutes} phút" if item.eta_minutes else "Đang cập nhật",
        "delivery_fee": item.delivery_fee,
        "delivery_fee_text": format_vnd(item.delivery_fee),
        "price": price,
        "price_text": format_vnd(price) if price else "",
        "rating": display_rating(item.rating),
        "review_count": item.review_count,
        "reason": item.reason,
        "score": round(float(item.score), 4),
        "is_best": index == 0,
    }
