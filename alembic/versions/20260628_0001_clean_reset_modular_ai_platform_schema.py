"""20260628_0001_clean_reset_modular_ai_platform_schema

Revision ID: 20260628_0001
Revises: 53ddba850e17
Create Date: 2026-06-28 00:00:00

Clean reset migration for the Modular AI Assistant Platform schema.

This migration is intentionally destructive for dev/demo databases: it drops
legacy tables and creates the new schema from PLAN.md and NEW_DB_SCHEMA.md.
Do not run it against production data without an external backup and a separate
production migration/backfill plan.
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "20260628_0001"
down_revision: Union[str, None] = "53ddba850e17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names() -> set[str]:
    if context.is_offline_mode():
        return set()
    return set(sa.inspect(op.get_bind()).get_table_names())


def _drop_table_if_exists(table_name: str, existing_tables: set[str]) -> None:
    if context.is_offline_mode() or table_name in existing_tables:
        bind = None if context.is_offline_mode() else op.get_bind()
        if bind is not None and bind.dialect.name == "postgresql":
            op.execute(sa.text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
        else:
            op.drop_table(table_name)
        existing_tables.discard(table_name)


def _drop_legacy_and_partial_platform_tables() -> None:
    existing_tables = _table_names()
    for table_name in [
        "notification_reads",
        "notifications",
        "admin_notifications",
        "user_assistant_settings",
        "user_feedback",
        "user_reviews",
        "payments",
        "executive_insight_reports",
        "fraud_signals",
        "operational_metric_snapshots",
        "charging_stations",
        "driver_status_snapshots",
        "trips",
        "drivers",
        "merchant_reviews",
        "merchant_metric_snapshots",
        "food_interactions",
        "food_request_logs",
        "user_food_profiles",
        "merchant_menu_items",
        "merchants",
        "food_catalog",
        "faq_cache_hits",
        "faq_candidates",
        "faq_question_variants",
        "faq_entries",
        "retrieval_events",
        "document_chunks",
        "documents",
        "knowledge_sources",
        "crawl_sources",
        "semantic_cache",
        "evaluation_runs",
        "evaluation_scores",
        "retrieval_logs",
        "rag_request_logs",
        "basic_request_logs",
        "system_logs",
        "error_logs",
        "conversation_summaries",
        "profile_snapshots",
        "memories",
        "user_memories",
        "user_profiles",
        "ai_trace_events",
        "tool_calls",
        "assistant_runs",
        "messages",
        "conversations",
        "persona_access_grants",
        "personas",
        "actor_identities",
        "actors",
        "guest_sessions",
        "users",
    ]:
        _drop_table_if_exists(table_name, existing_tables)


def _create_identity_tables() -> None:
    op.create_table(
        "actors",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_type", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_actors_actor_type_status", "actors", ["actor_type", "status"])
    op.create_index("ix_actors_email", "actors", ["email"], unique=True)

    op.create_table(
        "personas",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_prompt_key", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "actor_identities",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_subject", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_actor_identities_provider_subject"),
    )
    op.create_index("ix_actor_identities_actor_id", "actor_identities", ["actor_id"])

    op.create_table(
        "persona_access_grants",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("persona_id", sa.String(), sa.ForeignKey("personas.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="viewer"),
        sa.Column("scope_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_persona_access_grants_actor_id", "persona_access_grants", ["actor_id"])
    op.create_index("ix_persona_access_grants_persona_id", "persona_access_grants", ["persona_id"])


def _create_conversation_runtime_tables() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("persona_id", sa.String(), sa.ForeignKey("personas.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("channel", sa.String(), nullable=False, server_default="web"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_conversations_actor_persona_updated", "conversations", ["actor_id", "persona_id", "updated_at"])

    op.create_table(
        "messages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("conversation_id", sa.String(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False, server_default="text"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"])

    op.create_table(
        "assistant_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("conversation_id", sa.String(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("message_id", sa.String(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("persona_id", sa.String(), sa.ForeignKey("personas.id"), nullable=False),
        sa.Column("intent", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="running"),
        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_assistant_runs_conversation_created", "assistant_runs", ["conversation_id", "created_at"])
    op.create_index("ix_assistant_runs_persona_status_created", "assistant_runs", ["persona_id", "status", "created_at"])

    op.create_table(
        "tool_calls",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("assistant_runs.id"), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column("tool_group", sa.String(), nullable=False),
        sa.Column("permission_status", sa.String(), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=True),
        sa.Column("output_json", sa.Text(), nullable=True),
        sa.Column("error_json", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tool_calls_run_tool", "tool_calls", ["run_id", "tool_name"])
    op.create_index("ix_tool_calls_group_created", "tool_calls", ["tool_group", "created_at"])

    op.create_table(
        "ai_trace_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("assistant_runs.id"), nullable=True),
        sa.Column("conversation_id", sa.String(), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("persona_id", sa.String(), nullable=True),
        sa.Column("node", sa.String(), nullable=False),
        sa.Column("event", sa.String(), nullable=False),
        sa.Column("level", sa.String(), nullable=False, server_default="INFO"),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_trace_events_run_created", "ai_trace_events", ["run_id", "created_at"])
    op.create_index("ix_ai_trace_events_level_node_created", "ai_trace_events", ["level", "node", "created_at"])


def _create_memory_tables() -> None:
    op.create_table(
        "memories",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("persona_id", sa.String(), sa.ForeignKey("personas.id"), nullable=True),
        sa.Column("conversation_id", sa.String(), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("message_id", sa.String(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("memory_type", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="nlu"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_memories_actor_scope_status", "memories", ["actor_id", "scope", "status"])
    op.create_index("ix_memories_persona_type", "memories", ["persona_id", "memory_type"])

    op.create_table(
        "profile_snapshots",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("persona_id", sa.String(), sa.ForeignKey("personas.id"), nullable=True),
        sa.Column("profile_json", sa.Text(), nullable=False),
        sa.Column("source_memory_ids_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_profile_snapshots_actor_persona", "profile_snapshots", ["actor_id", "persona_id"])

    op.create_table(
        "conversation_summaries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("conversation_id", sa.String(), sa.ForeignKey("conversations.id"), nullable=False, unique=True),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("last_message_id", sa.String(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def _create_knowledge_and_faq_tables() -> None:
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("access_scope", sa.String(), nullable=False),
        sa.Column("crawl_strategy", sa.String(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_status", sa.String(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source_id", sa.String(), sa.ForeignKey("knowledge_sources.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("document_type", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False, server_default="vi"),
        sa.Column("content_hash", sa.String(), nullable=False, unique=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("document_id", sa.String(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("section_title", sa.String(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("vector_collection", sa.String(), nullable=True),
        sa.Column("vector_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_document_chunks_document_index", "document_chunks", ["document_id", "chunk_index"])
    op.create_index("ix_document_chunks_vector", "document_chunks", ["vector_collection", "vector_id"])

    op.create_table(
        "retrieval_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("assistant_runs.id"), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("retriever_name", sa.String(), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("results_json", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "faq_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("persona_id", sa.String(), sa.ForeignKey("personas.id"), nullable=False),
        sa.Column("canonical_question", sa.Text(), nullable=False),
        sa.Column("canonical_answer", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("source_version", sa.String(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_faq_entries_persona_scope_status", "faq_entries", ["persona_id", "scope", "status"])
    op.create_index("ix_faq_entries_intent_status", "faq_entries", ["intent", "status"])
    op.create_index("ix_faq_entries_effective_expires", "faq_entries", ["effective_from", "expires_at"])

    op.create_table(
        "faq_question_variants",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("faq_entry_id", sa.String(), sa.ForeignKey("faq_entries.id"), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("normalized_question", sa.Text(), nullable=False),
        sa.Column("language", sa.String(), nullable=False, server_default="vi"),
        sa.Column("vector_collection", sa.String(), nullable=True),
        sa.Column("vector_id", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_faq_question_variants_entry", "faq_question_variants", ["faq_entry_id"])
    op.create_index("ix_faq_question_variants_vector", "faq_question_variants", ["vector_collection", "vector_id"])

    op.create_table(
        "faq_candidates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("assistant_runs.id"), nullable=True),
        sa.Column("persona_id", sa.String(), nullable=True),
        sa.Column("user_query", sa.Text(), nullable=False),
        sa.Column("canonical_question", sa.Text(), nullable=False),
        sa.Column("proposed_answer", sa.Text(), nullable=True),
        sa.Column("eligibility_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="candidate"),
        sa.Column("reasons_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_faq_candidates_status_score", "faq_candidates", ["status", "eligibility_score"])

    op.create_table(
        "faq_cache_hits",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("assistant_runs.id"), nullable=True),
        sa.Column("faq_entry_id", sa.String(), sa.ForeignKey("faq_entries.id"), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("hybrid_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("semantic_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("keyword_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("matcher_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_faq_cache_hits_run_decision", "faq_cache_hits", ["run_id", "decision"])
    op.create_index("ix_faq_cache_hits_entry_created", "faq_cache_hits", ["faq_entry_id", "created_at"])


def _create_food_merchant_tables() -> None:
    op.create_table(
        "merchants",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("owner_actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("open_hours_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_merchants_city_status", "merchants", ["city", "status"])

    op.create_table(
        "merchant_menu_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("item_id", sa.String(), nullable=True, unique=True),
        sa.Column("merchant_id", sa.String(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("merchant_name", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("cuisine", sa.String(), nullable=True),
        sa.Column("taste_tags_json", sa.Text(), nullable=True),
        sa.Column("diet_tags_json", sa.Text(), nullable=True),
        sa.Column("ingredient_tags_json", sa.Text(), nullable=True),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("discount_percent", sa.Integer(), nullable=True),
        sa.Column("final_price", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(), nullable=False, server_default="VND"),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("tags_json", sa.Text(), nullable=True),
        sa.Column("merchant_rating", sa.Float(), nullable=True),
        sa.Column("merchant_review_count", sa.Integer(), nullable=True),
        sa.Column("merchant_address", sa.Text(), nullable=True),
        sa.Column("merchant_lat", sa.Float(), nullable=True),
        sa.Column("merchant_lng", sa.Float(), nullable=True),
        sa.Column("merchant_open_hours_json", sa.Text(), nullable=True),
        sa.Column("avg_prep_minutes", sa.Float(), nullable=True),
        sa.Column("base_delivery_fee", sa.Integer(), nullable=True),
        sa.Column("fee_per_km", sa.Integer(), nullable=True),
        sa.Column("service_radius_km", sa.Float(), nullable=True),
        sa.Column("source", sa.String(), nullable=True, server_default="shopeefood"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("city_slug", sa.String(), nullable=True),
        sa.Column("raw_ref", sa.String(), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_merchant_menu_items_item_id", "merchant_menu_items", ["item_id"], unique=True)
    op.create_index("ix_merchant_menu_items_merchant_status", "merchant_menu_items", ["merchant_id", "status"])

    op.create_table(
        "food_interactions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("conversation_id", sa.String(), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("message_id", sa.String(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("merchant_id", sa.String(), sa.ForeignKey("merchants.id"), nullable=True),
        sa.Column("menu_item_id", sa.String(), sa.ForeignKey("merchant_menu_items.id"), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("rank_position", sa.Integer(), nullable=True),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("context_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "merchant_metric_snapshots",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("merchant_id", sa.String(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("orders_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("gross_revenue", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("net_revenue", sa.Integer(), nullable=True),
        sa.Column("avg_rating", sa.Float(), nullable=True),
        sa.Column("cancel_rate", sa.Float(), nullable=True),
        sa.Column("prep_time_avg_minutes", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_merchant_metric_snapshots_merchant_date", "merchant_metric_snapshots", ["merchant_id", "snapshot_date"])

    op.create_table(
        "merchant_reviews",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("merchant_id", sa.String(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("menu_item_id", sa.String(), sa.ForeignKey("merchant_menu_items.id"), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.String(), nullable=True),
        sa.Column("topics_json", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )


def _create_ride_driver_ops_tables() -> None:
    op.create_table(
        "drivers",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("vehicle_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "trips",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("customer_actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("driver_id", sa.String(), sa.ForeignKey("drivers.id"), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("pickup_address", sa.Text(), nullable=True),
        sa.Column("pickup_lat", sa.Float(), nullable=True),
        sa.Column("pickup_lng", sa.Float(), nullable=True),
        sa.Column("dropoff_address", sa.Text(), nullable=True),
        sa.Column("dropoff_lat", sa.Float(), nullable=True),
        sa.Column("dropoff_lng", sa.Float(), nullable=True),
        sa.Column("estimated_fare", sa.Integer(), nullable=True),
        sa.Column("final_fare", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_trips_driver_status_created", "trips", ["driver_id", "status", "created_at"])

    op.create_table(
        "driver_status_snapshots",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("driver_id", sa.String(), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("battery_percent", sa.Integer(), nullable=True),
        sa.Column("current_trip_id", sa.String(), sa.ForeignKey("trips.id"), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_driver_status_snapshots_driver_created", "driver_status_snapshots", ["driver_id", "created_at"])

    op.create_table(
        "charging_stations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("available_ports", sa.Integer(), nullable=True),
        sa.Column("total_ports", sa.Integer(), nullable=True),
        sa.Column("price_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="unknown"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "operational_metric_snapshots",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("metric_name", sa.String(), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("dimension_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_operational_metric_snapshots_date_region_name", "operational_metric_snapshots", ["metric_date", "region", "metric_name"])

    op.create_table(
        "fraud_signals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("driver_id", sa.String(), sa.ForeignKey("drivers.id"), nullable=True),
        sa.Column("trip_id", sa.String(), sa.ForeignKey("trips.id"), nullable=True),
        sa.Column("signal_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "executive_insight_reports",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("insight_type", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("data_json", sa.Text(), nullable=True),
        sa.Column("created_by_run_id", sa.String(), sa.ForeignKey("assistant_runs.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )


def _create_payment_notification_feedback_tables() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("trip_id", sa.String(), sa.ForeignKey("trips.id"), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="VND"),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("provider_ref", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("audience_type", sa.String(), nullable=False),
        sa.Column("audience_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("created_by_actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "notification_reads",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("notification_id", sa.String(), sa.ForeignKey("notifications.id"), nullable=False),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("notification_id", "actor_id", name="uq_notification_reads_notification_actor"),
    )

    op.create_table(
        "user_feedback",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("assistant_runs.id"), nullable=True),
        sa.Column("message_id", sa.String(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("rating", sa.String(), nullable=False),
        sa.Column("reason_tags_json", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )


def _create_evaluation_tables() -> None:
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_name", sa.String(), nullable=False),
        sa.Column("dataset_name", sa.String(), nullable=True),
        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="completed"),
        sa.Column("average_latency_sec", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recall_5", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recall_10", sa.Float(), nullable=False, server_default="0"),
        sa.Column("mrr", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ndcg_5", sa.Float(), nullable=False, server_default="0"),
        sa.Column("faithfulness", sa.Float(), nullable=False, server_default="0"),
        sa.Column("correctness", sa.Float(), nullable=False, server_default="0"),
        sa.Column("relevancy", sa.Float(), nullable=False, server_default="0"),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_evaluation_runs_run_name", "evaluation_runs", ["run_name"])
    op.create_index("ix_evaluation_runs_status", "evaluation_runs", ["status"])


def _seed_base_personas() -> None:
    now = datetime.utcnow()
    personas = sa.table(
        "personas",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("default_prompt_key", sa.String),
        sa.column("enabled", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        personas,
        [
            {
                "id": "customer",
                "name": "Customer AI Assistant",
                "description": "Assistant for customer journeys, RAG, food, ride, travel, booking, and payment guidance.",
                "default_prompt_key": "customer_persona",
                "enabled": True,
                "created_at": now,
            },
            {
                "id": "driver",
                "name": "Driver Copilot",
                "description": "Copilot for drivers: trip status, ETA, charging, hot zones, and KPI support.",
                "default_prompt_key": "driver_persona",
                "enabled": True,
                "created_at": now,
            },
            {
                "id": "merchant",
                "name": "Merchant Copilot",
                "description": "AI COO for merchants: revenue, menu, reviews, promotion, and business consulting.",
                "default_prompt_key": "merchant_persona",
                "enabled": True,
                "created_at": now,
            },
            {
                "id": "operator",
                "name": "Operator Copilot",
                "description": "Internal operations assistant for fleet, incidents, fraud, and revenue diagnostics.",
                "default_prompt_key": "operator_persona",
                "enabled": True,
                "created_at": now,
            },
            {
                "id": "executive",
                "name": "Executive AI",
                "description": "Business intelligence copilot for strategic decisions, forecasts, churn, and expansion.",
                "default_prompt_key": "executive_persona",
                "enabled": True,
                "created_at": now,
            },
        ],
    )


def upgrade() -> None:
    _drop_legacy_and_partial_platform_tables()
    _create_identity_tables()
    _create_conversation_runtime_tables()
    _create_memory_tables()
    _create_knowledge_and_faq_tables()
    _create_food_merchant_tables()
    _create_ride_driver_ops_tables()
    _create_payment_notification_feedback_tables()
    _create_evaluation_tables()
    _seed_base_personas()


def downgrade() -> None:
    existing_tables = _table_names()
    for table_name in [
        "notification_reads",
        "notifications",
        "user_feedback",
        "payments",
        "evaluation_runs",
        "executive_insight_reports",
        "fraud_signals",
        "operational_metric_snapshots",
        "charging_stations",
        "driver_status_snapshots",
        "trips",
        "drivers",
        "merchant_reviews",
        "merchant_metric_snapshots",
        "food_interactions",
        "merchant_menu_items",
        "merchants",
        "faq_cache_hits",
        "faq_candidates",
        "faq_question_variants",
        "faq_entries",
        "retrieval_events",
        "document_chunks",
        "documents",
        "knowledge_sources",
        "conversation_summaries",
        "profile_snapshots",
        "memories",
        "ai_trace_events",
        "tool_calls",
        "assistant_runs",
        "messages",
        "conversations",
        "persona_access_grants",
        "actor_identities",
        "personas",
        "actors",
    ]:
        _drop_table_if_exists(table_name, existing_tables)
