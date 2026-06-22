"""add_summary_json_to_conversation_summaries

Revision ID: 9619f1a603b6
Revises: 20260621_0003
Create Date: 2026-06-22 05:22:24.251328+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '9619f1a603b6'
down_revision: Union[str, None] = '20260621_0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('conversation_summaries', sa.Column('summary_json', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('conversation_summaries', 'summary_json')
