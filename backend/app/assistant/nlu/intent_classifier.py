from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import re
from typing import Any

from app.assistant.prompts.nlu_prompts import NLU_INTENT_REWRITE_PROMPT
from app.config.settings import settings


logger = logging.getLogger(__name__)

VALID_INTENTS = {
    "small_talk",
    "missing_info",
    "sensitive",
    "rag",
    "food_recommendation",
    "ride_support",
    "driver_support",
    "merchant_analytics",
    "operations_monitoring",
    "executive_insight",
}

ALIASES = {
    "small-talk": "small_talk",
    "food": "food_recommendation",
    "ride": "ride_support",
    "operator": "operations_monitoring",
    "merchant": "merchant_analytics",
    "executive": "executive_insight",
    "driver": "driver_support",
}


@dataclass(frozen=True)
class NLUResult:
    intent: str
    rewritten_query: str
    confidence: float = 0.0
    suggested_answer: str | None = None


def _extract_json(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("NLU response is not a JSON object")
    return payload


def _chat_model():
    try:
        from langchain_openai import ChatOpenAI
    except ModuleNotFoundError:
        return None

    model = settings.NLU_MODEL or settings.RAG_ANSWER_MODEL
    if settings.GROQ_API_KEY and any(token in model.lower() for token in ("llama", "mixtral", "gemma")):
        return ChatOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            model=model,
            temperature=0,
            max_tokens=600,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )
    if settings.OPENAI_API_KEY:
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=model,
            temperature=0,
            max_tokens=600,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )
    return None


def analyze_intent(
    query: str,
    persona: str = "customer",
    *,
    recent_turns: list[dict[str, str]] | None = None,
    memories: list[dict[str, object]] | None = None,
    profile: dict[str, Any] | None = None,
) -> NLUResult:
    chat = _chat_model()
    if chat is None:
        logger.warning("NLU LLM is not configured; falling back to rag intent")
        return NLUResult(intent="rag", rewritten_query=" ".join(query.strip().split()))

    user_payload = {
        "persona": persona,
        "recent_turns": recent_turns or [],
        "memories": memories or [],
        "profile": profile or {},
        "CURRENT_QUERY": query,
    }
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        response = chat.invoke(
            [
                SystemMessage(content=NLU_INTENT_REWRITE_PROMPT),
                HumanMessage(content=json.dumps(user_payload, ensure_ascii=False, default=str)),
            ]
        )
        payload = _extract_json(str(response.content or ""))
    except Exception as exc:
        logger.warning("NLU LLM failed; falling back to rag intent: %s", exc)
        return NLUResult(intent="rag", rewritten_query=" ".join(query.strip().split()))

    intent = str(payload.get("intent") or "rag").strip()
    intent = ALIASES.get(intent, intent)
    if intent not in VALID_INTENTS:
        logger.warning("NLU returned unknown intent %r; using rag", intent)
        intent = "rag"

    rewritten_query = str(payload.get("rewritten_query") or query).strip() or query
    suggested_answer = payload.get("suggested_answer")
    if suggested_answer is not None:
        suggested_answer = str(suggested_answer).strip() or None
    if intent not in {"small_talk", "sensitive", "missing_info"}:
        suggested_answer = None

    try:
        confidence = float(payload.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0

    return NLUResult(intent=intent, rewritten_query=rewritten_query, confidence=confidence, suggested_answer=suggested_answer)


def classify_intent(query: str, persona: str = "customer") -> str:
    return analyze_intent(query, persona).intent
