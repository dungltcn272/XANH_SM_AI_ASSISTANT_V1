"""add user_id and guest_id to conversation_summaries

Revision ID: 20260621_0003
Revises: 20260621_0002
Create Date: 2026-06-21 17:25:00
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import context, op

revision: str = "20260621_0003"
down_revision: Union[str, None] = "20260621_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
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
    if not _has_column("conversation_summaries", "user_id"):
        op.add_column("conversation_summaries", sa.Column("user_id", sa.String(), nullable=True))
        op.create_index("ix_conversation_summaries_user_id", "conversation_summaries", ["user_id"])
    if not _has_column("conversation_summaries", "guest_id"):
        op.add_column("conversation_summaries", sa.Column("guest_id", sa.String(), nullable=True))
        op.create_index("ix_conversation_summaries_guest_id", "conversation_summaries", ["guest_id"])


def downgrade() -> None:
    if _has_column("conversation_summaries", "guest_id"):
        op.drop_index("ix_conversation_summaries_guest_id", table_name="conversation_summaries")
        op.drop_column("conversation_summaries", "guest_id")
    if _has_column("conversation_summaries", "user_id"):
        op.drop_index("ix_conversation_summaries_user_id", table_name="conversation_summaries")
        op.drop_column("conversation_summaries", "user_id")
