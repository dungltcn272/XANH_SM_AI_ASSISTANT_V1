from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from app.food_recommendation.payloads import display_rating, format_food_answer
from app.core.config import settings as config
from app.core.logger import log_warn
from app.prompts import FOOD_RECOMMENDER_ANSWER_SYSTEM_PROMPT


def compose_food_answer_with_llm(
    items: list[Any],
    query: str,
    slots: Any,
    food_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
        return fallback
    if (not config.OPENAI_API_KEY and not config.GROQ_API_KEY) or config.EMBEDDING_PROVIDER == "mock" or ("YOUR_OPENAI_API_KEY" in config.OPENAI_API_KEY and not config.GROQ_API_KEY):
        return fallback

    recommended_items = []
    for item in items[:8]:
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
    try:
        model_to_use = config.FOOD_ANSWER_MODEL
        if config.GROQ_API_KEY and model_to_use != "gpt-4o-mini" and model_to_use != "gpt-4o":
            client = OpenAI(api_key=config.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1", timeout=config.OPENAI_TIMEOUT_SECONDS)
        else:
            client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.OPENAI_TIMEOUT_SECONDS)

        response = client.chat.completions.create(
            model=model_to_use,
            messages=[
                {"role": "system", "content": FOOD_RECOMMENDER_ANSWER_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            temperature=0.25,
            max_tokens=520,
            response_format={"type": "json_object"}
        )
        content = (response.choices[0].message.content or "").strip()
        content = re.sub(r"^```json|```$", "", content).strip()
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return fallback

        allowed_ids = {item.item_id for item in items[:8]}
        notes = []
        for note in parsed.get("item_notes") or []:
            if isinstance(note, dict) and note.get("item_id") in allowed_ids:
                notes.append({
                    "item_id": note.get("item_id"),
                    "advice": str(note.get("advice") or "").strip()[:240],
                })

        answer = str(parsed.get("answer") or "").strip() or fallback_answer
        return {
            "answer": answer,
            "cards_title": str(parsed.get("cards_title") or "").strip() or None,
            "cards_subtitle": str(parsed.get("cards_subtitle") or "").strip() or None,
            "item_notes": notes,
            "llm_used": True,
            "error": None,
        }
    except Exception as exc:
        log_warn("FOOD", f"Food answer LLM failed: {exc}")
        fallback["error"] = str(exc)
        return fallback

