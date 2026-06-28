from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.cache.hybrid_cache_matcher import FaqEntrySnapshot, FaqMatchScore, score_faq_match


class FaqRepository(Protocol):
    def list_published_candidates(self, persona_id: str, intent: str) -> list[FaqEntrySnapshot]:
        ...

    def save_cache_decision(self, match: FaqMatchScore, query: str, run_id: str | None = None) -> None:
        ...


@dataclass(frozen=True)
class FaqCacheResult:
    hit: bool
    answer: str | None
    match: FaqMatchScore | None


class CuratedFaqCache:
    def __init__(self, repository: FaqRepository):
        self.repository = repository

    def get(
        self,
        query: str,
        persona_id: str,
        intent: str,
        semantic_scores: dict[str, float] | None = None,
        run_id: str | None = None,
    ) -> FaqCacheResult:
        semantic_scores = semantic_scores or {}
        best_match: FaqMatchScore | None = None
        best_entry: FaqEntrySnapshot | None = None

        for entry in self.repository.list_published_candidates(persona_id=persona_id, intent=intent):
            match = score_faq_match(
                query=query,
                entry=entry,
                persona_id=persona_id,
                intent=intent,
                semantic_score=semantic_scores.get(entry.faq_id, 0.0),
            )
            if best_match is None or match.hybrid_score > best_match.hybrid_score:
                best_match = match
                best_entry = entry

        if best_match is None:
            return FaqCacheResult(hit=False, answer=None, match=None)

        self.repository.save_cache_decision(best_match, query=query, run_id=run_id)
        if best_match.decision == "hit" and best_entry is not None:
            return FaqCacheResult(hit=True, answer=best_entry.canonical_answer, match=best_match)
        return FaqCacheResult(hit=False, answer=None, match=best_match)
