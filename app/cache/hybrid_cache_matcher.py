from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date


TOKEN_PATTERN = re.compile(r"[\wÀ-ỹ]+", re.UNICODE)


@dataclass(frozen=True)
class FaqEntrySnapshot:
    faq_id: str
    persona_id: str
    canonical_question: str
    canonical_answer: str
    intent: str
    scope: str
    status: str
    effective_from: date | None = None
    expires_at: date | None = None
    variants: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FaqMatchScore:
    faq_id: str
    decision: str
    hybrid_score: float
    semantic_score: float
    keyword_score: float
    reasons: tuple[str, ...]


def normalize_for_match(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def keyword_overlap_score(query: str, candidate: str) -> float:
    query_tokens = set(TOKEN_PATTERN.findall(normalize_for_match(query)))
    candidate_tokens = set(TOKEN_PATTERN.findall(normalize_for_match(candidate)))
    if not query_tokens or not candidate_tokens:
        return 0.0
    return len(query_tokens & candidate_tokens) / max(1, len(query_tokens))


def _is_fresh(entry: FaqEntrySnapshot, today: date | None) -> bool:
    if today is None:
        today = date.today()
    if entry.effective_from and entry.effective_from > today:
        return False
    if entry.expires_at and entry.expires_at < today:
        return False
    return True


def score_faq_match(
    query: str,
    entry: FaqEntrySnapshot,
    persona_id: str,
    intent: str,
    semantic_score: float = 0.0,
    today: date | None = None,
) -> FaqMatchScore:
    reasons: list[str] = []

    if entry.status != "published":
        reasons.append("faq_not_published")
    if entry.persona_id != persona_id:
        reasons.append("persona_scope_mismatch")
    if entry.intent != intent:
        reasons.append("intent_mismatch")
    if not _is_fresh(entry, today):
        reasons.append("faq_not_effective_or_expired")

    candidate_texts = (entry.canonical_question, *entry.variants)
    keyword_score = max(keyword_overlap_score(query, candidate) for candidate in candidate_texts)
    exact_score = 1.0 if normalize_for_match(query) in {normalize_for_match(text) for text in candidate_texts} else 0.0
    hybrid_score = max(exact_score, (0.6 * semantic_score) + (0.4 * keyword_score))

    if hybrid_score < 0.86:
        reasons.append("hybrid_score_too_low")
    if semantic_score and semantic_score < 0.82:
        reasons.append("semantic_score_too_low")
    if keyword_score < 0.45:
        reasons.append("keyword_score_too_low")

    decision = "hit" if not reasons else "miss"
    if "persona_scope_mismatch" in reasons:
        decision = "blocked_scope"
    elif "faq_not_effective_or_expired" in reasons:
        decision = "expired"
    elif "hybrid_score_too_low" in reasons:
        decision = "low_score"

    return FaqMatchScore(
        faq_id=entry.faq_id,
        decision=decision,
        hybrid_score=round(hybrid_score, 4),
        semantic_score=round(semantic_score, 4),
        keyword_score=round(keyword_score, 4),
        reasons=tuple(reasons),
    )
