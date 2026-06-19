from __future__ import annotations

import json
from typing import Any

from app.core.config import settings as config
from app.core.llm import get_llm_client
from app.core.logger import log_warn
from app.food_recommendation.payloads import (
    display_rating,
    distance_text,
    format_food_answer,
    format_vnd,
    food_recommendations_payload,
)
from app.memory.context_builder import ContextBuilder
from app.prompts import FOOD_RECOMMENDER_ANSWER_SYSTEM_PROMPT

CARD_START = "[[FOOD_CARD"
CARD_END = "]]"


def stream_food_answer_with_llm(
    items: list[Any],
    query: str,
    slots: Any,
    food_context: dict[str, Any] | None = None,
    chat_history: list[dict[str, str]] | None = None,
    assistant_context: dict[str, Any] | None = None,
):
    fallback_answer = format_food_answer(items, slots.category)
    fallback_cards = food_recommendations_payload(items, slots.category, query) if items else None
    fallback = {
        "answer": fallback_answer,
        "food_cards": fallback_cards,
        "food_card_count": len((fallback_cards or {}).get("items") or []),
        "food_cards_source": "ranked_items_fallback" if fallback_cards else "none",
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
    candidate_by_id = {
        str(item["item_id"]): item
        for item in recommended_items
        if item.get("item_id")
    }

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
            max_tokens=900,
            stream=True,
        )

        parser = _FoodCardStreamParser(candidate_by_id)
        final_answer = ""
        cards: list[dict[str, Any]] = []

        for chunk in response:
            text = chunk.choices[0].delta.content
            if not text:
                continue
            for event in parser.feed(text):
                if event["type"] == "text":
                    final_answer += event["text"]
                    yield {"type": "chunk", "text": event["text"]}
                elif event["type"] == "card":
                    cards.append(event["card"])
                    yield {"type": "food_card", "card": event["card"]}

        for event in parser.flush():
            if event["type"] == "text":
                final_answer += event["text"]
                yield {"type": "chunk", "text": event["text"]}
            elif event["type"] == "card":
                cards.append(event["card"])
                yield {"type": "food_card", "card": event["card"]}

        answer_meta = {
            "answer": final_answer.strip() or fallback_answer,
            "food_cards": _cards_payload(cards, slots.category, query),
            "food_card_count": len(cards),
            "food_cards_source": "llm_marker" if cards else "none",
            "llm_used": True,
            "error": None,
        }
        yield {"type": "done", "answer_meta": answer_meta}

    except Exception as exc:
        log_warn("FOOD", f"Error generating food answer: {exc}")
        fallback["error"] = str(exc)
        yield {"type": "done", "answer_meta": fallback}


class _FoodCardStreamParser:
    def __init__(self, candidate_by_id: dict[str, dict[str, Any]]):
        self.candidate_by_id = candidate_by_id
        self.buffer = ""
        self.in_card = False

    def feed(self, text: str) -> list[dict[str, Any]]:
        self.buffer += text
        events: list[dict[str, Any]] = []

        while self.buffer:
            if not self.in_card:
                start = self.buffer.find(CARD_START)
                if start == -1:
                    safe_len = max(0, len(self.buffer) - len(CARD_START) + 1)
                    if safe_len:
                        events.append({"type": "text", "text": self.buffer[:safe_len]})
                        self.buffer = self.buffer[safe_len:]
                    break
                if start > 0:
                    events.append({"type": "text", "text": self.buffer[:start]})
                    self.buffer = self.buffer[start:]
                self.in_card = True

            end = self.buffer.find(CARD_END)
            if end == -1:
                break

            marker = self.buffer[: end + len(CARD_END)]
            self.buffer = self.buffer[end + len(CARD_END):]
            self.in_card = False
            card = self._parse_marker(marker)
            if card:
                events.append({"type": "card", "card": card})

        return events

    def flush(self) -> list[dict[str, Any]]:
        if not self.buffer:
            return []
        if self.in_card:
            card = self._parse_marker(self.buffer)
            self.buffer = ""
            self.in_card = False
            return [{"type": "card", "card": card}] if card else []
        text = self.buffer
        self.buffer = ""
        return [{"type": "text", "text": text}]

    def _parse_marker(self, marker: str) -> dict[str, Any] | None:
        raw = marker.strip()
        if raw.startswith(CARD_START):
            raw = raw[len(CARD_START):]
        if raw.endswith(CARD_END):
            raw = raw[: -len(CARD_END)]
        raw = raw.strip()
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        item_id = str(parsed.get("item_id") or "")
        base = self.candidate_by_id.get(item_id)
        if not base:
            return None
        return _merge_card(base, parsed)


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


def _merge_card(base: dict[str, Any], llm_item: dict[str, Any]) -> dict[str, Any]:
    def pick(key: str) -> Any:
        value = llm_item.get(key)
        return base.get(key) if value in (None, "") else value

    return {
        "item_id": base.get("item_id"),
        "name": pick("name"),
        "dish_name": pick("dish_name"),
        "address": pick("address"),
        "image_url": pick("image_url"),
        "order_url": pick("order_url"),
        "rating": pick("rating"),
        "review_count": pick("review_count"),
        "distance_km": pick("distance_km"),
        "distance_text": pick("distance_text"),
        "eta_minutes": pick("eta_minutes"),
        "eta_text": pick("eta_text"),
        "delivery_fee": pick("delivery_fee"),
        "delivery_fee_text": pick("delivery_fee_text"),
        "price": pick("price"),
        "price_text": pick("price_text"),
        "reason": pick("reason"),
        "advice": llm_item.get("advice"),
        "is_best": bool(llm_item.get("is_best", base.get("is_best"))),
    }


def _cards_payload(cards: list[dict[str, Any]], category: str | None, query: str | None) -> dict[str, Any]:
    title = "Một vài quán phù hợp gần anh/chị"
    if category:
        title = f"Một vài quán {category} phù hợp gần anh/chị"
    return {
        "title": title,
        "subtitle": "Các card được tạo ngay trong lúc AI trả lời, dựa trên kết quả tìm kiếm phù hợp.",
        "query": query,
        "items": cards,
        "more_items": [],
    }
