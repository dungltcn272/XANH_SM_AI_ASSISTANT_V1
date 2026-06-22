"""add_timestamps_to_conversation_summaries

Revision ID: 53ddba850e17
Revises: 9619f1a603b6
Create Date: 2026-06-22 07:14:35.400398+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '53ddba850e17'
down_revision: Union[str, None] = '9619f1a603b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def _has_column(table_name: str, column_name: str) -> bool:
    from alembic import context
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        columns = [col["name"] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False

def upgrade() -> None:
    if not _has_column("conversation_summaries", "created_at"):
        op.add_column("conversation_summaries", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    if not _has_column("conversation_summaries", "updated_at"):
        op.add_column("conversation_summaries", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        op.create_index("ix_conversation_summaries_updated_at", "conversation_summaries", ["updated_at"])


def downgrade() -> None:
    if _has_column("conversation_summaries", "updated_at"):
        op.drop_index("ix_conversation_summaries_updated_at", table_name="conversation_summaries")
        op.drop_column("conversation_summaries", "updated_at")
    if _has_column("conversation_summaries", "created_at"):
        op.drop_column("conversation_summaries", "created_at")
