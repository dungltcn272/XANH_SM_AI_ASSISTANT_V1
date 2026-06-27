from __future__ import annotations

import re
from dataclasses import dataclass, field


PHONE_PATTERN = re.compile(r"(\+?\d[\d\s.\-]{7,}\d)")
EMAIL_PATTERN = re.compile(r"[\w.\-+]+@[\w.\-]+\.\w+")
SECRET_PATTERN = re.compile(r"(api[_-]?key|token|password|secret)\s*[:=]", re.IGNORECASE)

TEMPORAL_WORDS = {
    "hôm nay",
    "hôm qua",
    "ngày mai",
    "bây giờ",
    "hiện tại",
    "cuốc này",
    "đơn này",
    "khách này",
    "tài xế này",
}

REALTIME_INTENTS = {
    "driver_status",
    "trip_status",
    "operator_metric",
    "executive_forecast",
    "payment_status",
    "merchant_live_metric",
}


@dataclass(frozen=True)
class FaqCandidateAnalysis:
    eligible: bool
    score: float
    canonical_question: str
    reasons: tuple[str, ...] = field(default_factory=tuple)


def normalize_question_text(query: str) -> str:
    return " ".join((query or "").strip().split())


def _contains_private_or_secret_data(text: str) -> bool:
    return bool(PHONE_PATTERN.search(text) or EMAIL_PATTERN.search(text) or SECRET_PATTERN.search(text))


def _contains_temporal_context(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in TEMPORAL_WORDS)


def analyze_faq_candidate(
    user_query: str,
    answer: str | None,
    intent: str | None,
    persona_id: str,
    source_ids: list[str] | None = None,
) -> FaqCandidateAnalysis:
    canonical_question = normalize_question_text(user_query)
    reasons: list[str] = []
    score = 1.0

    if len(canonical_question) < 12:
        reasons.append("query_too_short")
        score -= 0.3

    if not answer or len(answer.strip()) < 24:
        reasons.append("answer_missing_or_too_short")
        score -= 0.35

    if _contains_private_or_secret_data(canonical_question):
        reasons.append("contains_private_or_secret_data")
        score -= 0.8

    if _contains_temporal_context(canonical_question):
        reasons.append("depends_on_temporal_or_instance_context")
        score -= 0.45

    if (intent or "").strip() in REALTIME_INTENTS:
        reasons.append("realtime_intent_not_cacheable")
        score -= 0.6

    if persona_id not in {"customer", "driver", "merchant", "operator", "executive"}:
        reasons.append("unknown_persona")
        score -= 0.2

    if not source_ids:
        reasons.append("missing_trusted_source")
        score -= 0.2

    final_score = max(0.0, min(1.0, score))
    return FaqCandidateAnalysis(
        eligible=final_score >= 0.72 and not any(reason.endswith("not_cacheable") for reason in reasons),
        score=final_score,
        canonical_question=canonical_question,
        reasons=tuple(reasons),
    )
