from __future__ import annotations

import json
from datetime import date
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.cache.faq_cache import FaqRepository
from app.cache.hybrid_cache_matcher import FaqEntrySnapshot, FaqMatchScore


class SqlAlchemyFaqRepository(FaqRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_published_candidates(self, persona_id: str, intent: str) -> list[FaqEntrySnapshot]:
        rows = self.db.execute(
            text(
                """
                SELECT
                    id,
                    persona_id,
                    canonical_question,
                    canonical_answer,
                    intent,
                    scope,
                    status,
                    effective_from,
                    expires_at
                FROM faq_entries
                WHERE persona_id = :persona_id
                  AND intent = :intent
                  AND status = 'published'
                """
            ),
            {"persona_id": persona_id, "intent": intent},
        ).mappings().all()

        if not rows:
            return []

        entry_ids = [row["id"] for row in rows]
        variant_rows = self.db.execute(
            text(
                """
                SELECT faq_entry_id, question_text
                FROM faq_question_variants
                WHERE faq_entry_id IN :entry_ids
                """
            ).bindparams(bindparam("entry_ids", expanding=True)),
            {"entry_ids": entry_ids},
        ).mappings().all()
        variants_by_entry: dict[str, list[str]] = {}
        for row in variant_rows:
            variants_by_entry.setdefault(row["faq_entry_id"], []).append(row["question_text"])

        return [
            FaqEntrySnapshot(
                faq_id=row["id"],
                persona_id=row["persona_id"],
                canonical_question=row["canonical_question"],
                canonical_answer=row["canonical_answer"],
                intent=row["intent"],
                scope=row["scope"],
                status=row["status"],
                effective_from=_as_date(row["effective_from"]),
                expires_at=_as_date(row["expires_at"]),
                variants=tuple(variants_by_entry.get(row["id"], [])),
            )
            for row in rows
        ]

    def save_cache_decision(self, match: FaqMatchScore, query: str, run_id: str | None = None) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO faq_cache_hits (
                    id,
                    run_id,
                    faq_entry_id,
                    query,
                    hybrid_score,
                    semantic_score,
                    keyword_score,
                    decision,
                    matcher_json,
                    created_at
                )
                VALUES (
                    :id,
                    :run_id,
                    :faq_entry_id,
                    :query,
                    :hybrid_score,
                    :semantic_score,
                    :keyword_score,
                    :decision,
                    :matcher_json,
                    CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "id": f"faqhit_{_safe_uuid_hex()}",
                "run_id": run_id,
                "faq_entry_id": match.faq_id,
                "query": query,
                "hybrid_score": match.hybrid_score,
                "semantic_score": match.semantic_score,
                "keyword_score": match.keyword_score,
                "decision": match.decision,
                "matcher_json": json.dumps({"reasons": list(match.reasons)}, ensure_ascii=False),
            },
        )
        self.db.commit()


def _as_date(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _safe_uuid_hex() -> str:
    import uuid

    return uuid.uuid4().hex
