"""initial schema

Revision ID: 20260620_0001
Revises:
Create Date: 2026-06-20 00:01:00
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260620_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from app.db.base import Base
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from app.db.base import Base
    from app.db import models  # noqa: F401

    Base.metadata.drop_all(bind=op.get_bind())
