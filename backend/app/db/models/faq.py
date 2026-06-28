from __future__ import annotations

from .common import *

class FaqEntry(Base):
    __tablename__ = "faq_entries"

    id = Column(String, primary_key=True, default=lambda: generate_id("faq"))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    canonical_question = Column(Text, nullable=False)
    canonical_answer = Column(Text, nullable=False)
    intent = Column(String, nullable=False, index=True)
    scope = Column(String, nullable=False, index=True)
    status = Column(String, default="draft", nullable=False, index=True)
    source_type = Column(String, nullable=True)
    source_id = Column(String, nullable=True)
    source_version = Column(String, nullable=True)
    effective_from = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)

class FaqQuestionVariant(Base):
    __tablename__ = "faq_question_variants"

    id = Column(String, primary_key=True, default=lambda: generate_id("faqvar"))
    faq_entry_id = Column(String, ForeignKey("faq_entries.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    normalized_question = Column(Text, nullable=False)
    language = Column(String, default="vi", nullable=False)
    vector_collection = Column(String, nullable=True, index=True)
    vector_id = Column(String, nullable=True, index=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class FaqCandidate(Base):
    __tablename__ = "faq_candidates"

    id = Column(String, primary_key=True, default=lambda: generate_id("faqcand"))
    run_id = Column(String, ForeignKey("assistant_runs.id"), nullable=True, index=True)
    persona_id = Column(String, nullable=True, index=True)
    user_query = Column(Text, nullable=False)
    canonical_question = Column(Text, nullable=False)
    proposed_answer = Column(Text, nullable=True)
    eligibility_score = Column(Float, default=0.0, index=True)
    status = Column(String, default="candidate", nullable=False, index=True)
    reasons_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

class FaqCacheHit(Base):
    __tablename__ = "faq_cache_hits"

    id = Column(String, primary_key=True, default=lambda: generate_id("faqhit"))
    run_id = Column(String, ForeignKey("assistant_runs.id"), nullable=True, index=True)
    faq_entry_id = Column(String, ForeignKey("faq_entries.id"), nullable=True, index=True)
    query = Column(Text, nullable=False)
    hybrid_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)
    keyword_score = Column(Float, default=0.0)
    decision = Column(String, nullable=False, index=True)
    matcher_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
