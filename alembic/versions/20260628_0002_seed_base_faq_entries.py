"""20260628_0002_seed_base_faq_entries

Revision ID: 20260628_0002
Revises: 20260628_0001
Create Date: 2026-06-28 00:10:00
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260628_0002"
down_revision: Union[str, None] = "20260628_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    now = datetime.utcnow()
    faq_entries = sa.table(
        "faq_entries",
        sa.column("id", sa.String),
        sa.column("persona_id", sa.String),
        sa.column("canonical_question", sa.Text),
        sa.column("canonical_answer", sa.Text),
        sa.column("intent", sa.String),
        sa.column("scope", sa.String),
        sa.column("status", sa.String),
        sa.column("source_type", sa.String),
        sa.column("source_id", sa.String),
        sa.column("source_version", sa.String),
        sa.column("effective_from", sa.Date),
        sa.column("expires_at", sa.Date),
        sa.column("metadata_json", sa.Text),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    faq_question_variants = sa.table(
        "faq_question_variants",
        sa.column("id", sa.String),
        sa.column("faq_entry_id", sa.String),
        sa.column("question_text", sa.Text),
        sa.column("normalized_question", sa.Text),
        sa.column("language", sa.String),
        sa.column("vector_collection", sa.String),
        sa.column("vector_id", sa.String),
        sa.column("metadata_json", sa.Text),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(
        faq_entries,
        [
            {
                "id": "faq_customer_food_recommendation",
                "persona_id": "customer",
                "canonical_question": "Xanh SM AI có thể gợi ý món ăn theo vị trí không?",
                "canonical_answer": (
                    "Có. Customer AI Assistant có thể gợi ý món/quán dựa trên vị trí, khẩu vị, ngân sách, "
                    "khoảng cách và các tín hiệu như rating hoặc ưu đãi. Nếu thiếu vị trí, hệ thống sẽ hỏi "
                    "anh/chị cung cấp hoặc xác nhận vị trí trước khi gợi ý."
                ),
                "intent": "rag",
                "scope": "customer",
                "status": "published",
                "source_type": "manual",
                "source_id": "seed_faq",
                "source_version": "20260628_0002",
                "effective_from": date(2026, 6, 28),
                "expires_at": None,
                "metadata_json": '{"seed": true, "cache_policy": "curated_faq_only"}',
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "faq_driver_copilot_scope",
                "persona_id": "driver",
                "canonical_question": "Driver Copilot hỗ trợ tài xế những việc gì?",
                "canonical_answer": (
                    "Driver Copilot hỗ trợ tài xế theo dõi trạng thái chuyến, vị trí khách, ETA, gợi ý trạm sạc, "
                    "khu vực nhu cầu cao và một số chỉ số vận hành. Những dữ liệu realtime cần được lấy từ tool "
                    "được cấp quyền, không dùng cache để trả thay."
                ),
                "intent": "rag",
                "scope": "driver",
                "status": "published",
                "source_type": "manual",
                "source_id": "seed_faq",
                "source_version": "20260628_0002",
                "effective_from": date(2026, 6, 28),
                "expires_at": None,
                "metadata_json": '{"seed": true, "cache_policy": "curated_faq_only"}',
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "faq_operator_copilot_scope",
                "persona_id": "operator",
                "canonical_question": "Operator Copilot dùng để làm gì?",
                "canonical_answer": (
                    "Operator Copilot là trợ lý AI cho đội vận hành nội bộ. Nó hỗ trợ theo dõi tài xế online, "
                    "doanh thu, khu vực thiếu tài xế, cảnh báo gian lận, sự cố và các tín hiệu điều phối. "
                    "Các số liệu realtime phải đến từ operational snapshots hoặc tool vận hành được cấp quyền."
                ),
                "intent": "rag",
                "scope": "operator",
                "status": "published",
                "source_type": "manual",
                "source_id": "seed_faq",
                "source_version": "20260628_0002",
                "effective_from": date(2026, 6, 28),
                "expires_at": None,
                "metadata_json": '{"seed": true, "cache_policy": "curated_faq_only"}',
                "created_at": now,
                "updated_at": now,
            },
        ],
    )
    op.bulk_insert(
        faq_question_variants,
        [
            {
                "id": "faqvar_customer_food_recommendation_1",
                "faq_entry_id": "faq_customer_food_recommendation",
                "question_text": "AI có gợi ý quán ăn gần tôi được không?",
                "normalized_question": "ai có gợi ý quán ăn gần tôi được không?",
                "language": "vi",
                "vector_collection": None,
                "vector_id": None,
                "metadata_json": '{"seed": true}',
                "created_at": now,
            },
            {
                "id": "faqvar_driver_copilot_scope_1",
                "faq_entry_id": "faq_driver_copilot_scope",
                "question_text": "Copilot tài xế làm được gì?",
                "normalized_question": "copilot tài xế làm được gì?",
                "language": "vi",
                "vector_collection": None,
                "vector_id": None,
                "metadata_json": '{"seed": true}',
                "created_at": now,
            },
            {
                "id": "faqvar_operator_copilot_scope_1",
                "faq_entry_id": "faq_operator_copilot_scope",
                "question_text": "Operator Copilot để làm gì?",
                "normalized_question": "operator copilot để làm gì?",
                "language": "vi",
                "vector_collection": None,
                "vector_id": None,
                "metadata_json": '{"seed": true}',
                "created_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM faq_question_variants WHERE id IN ("
        "'faqvar_customer_food_recommendation_1',"
        "'faqvar_driver_copilot_scope_1',"
        "'faqvar_operator_copilot_scope_1'"
        ")"
    )
    op.execute(
        "DELETE FROM faq_entries WHERE id IN ("
        "'faq_customer_food_recommendation',"
        "'faq_driver_copilot_scope',"
        "'faq_operator_copilot_scope'"
        ")"
    )
