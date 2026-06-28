from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.assistant.prompts.food_prompts import FOOD_SYSTEM_PROMPT
from app.config.settings import settings
from app.domains.food.candidate_generator import generate_food_candidates
from app.domains.food.food_profile import get_food_profile
from app.domains.food.geocode import geocode_address
from app.domains.food.ranker import rank_food_candidates
from app.domains.food.schemas import FoodCandidate, FoodSearchContext
from app.integrations.openai_client import complete_text, openai_configured


def _food_answer(query: str, items: list[FoodCandidate], profile: dict) -> str:
    if not items:
        return "Mình chưa tìm được món phù hợp. Bạn có thể cung cấp vị trí hoặc món muốn ăn cụ thể hơn không?"
    payload = [item.model_dump() for item in items[:5]]
    if openai_configured():
        answer = complete_text(
            system_prompt=FOOD_SYSTEM_PROMPT,
            user_prompt=f"QUERY:\n{query}\n\nUSER_PROFILE:\n{json.dumps(profile, ensure_ascii=False)}\n\nRECOMMENDED_ITEMS:\n{json.dumps(payload, ensure_ascii=False)}",
            model=settings.FOOD_ANSWER_MODEL,
            temperature=0.35,
            max_tokens=900,
        )
        if answer:
            return answer
    top = items[0]
    return f"Mình gợi ý **{top.name}** từ {top.merchant_name or 'quán phù hợp'} vì khớp nhu cầu, rating ổn và nằm trong nhóm ứng viên tốt nhất."


def recommend_food(
    query: str,
    *,
    db: Session | None = None,
    actor_id: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    address: str | None = None,
    budget_vnd: int | None = None,
    limit: int = 8,
) -> dict:
    geocoded = geocode_address(address)
    context = FoodSearchContext(
        actor_id=actor_id,
        query=query,
        lat=lat if lat is not None else (geocoded or {}).get("lat"),
        lng=lng if lng is not None else (geocoded or {}).get("lng"),
        address=address,
        budget_vnd=budget_vnd,
    )
    profile = get_food_profile(db, actor_id)
    candidates = generate_food_candidates(query, db=db, context=context, limit=limit)
    ranked = rank_food_candidates(candidates, context=context, limit=limit)
    answer = _food_answer(query, ranked, profile)
    return {
        "answer": answer,
        "items": [item.model_dump() for item in ranked],
        "context": context.model_dump(),
        "profile": profile,
        "source": "merchant_menu_items_or_jsonl",
    }
