"""add notifications and assistant personas

Revision ID: 20260621_0002
Revises: 20260620_0001
Create Date: 2026-06-21 11:20:00
"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import context, op


revision: str = "20260621_0002"
down_revision: Union[str, None] = "20260620_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
    if not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    if not _has_table("user_assistant_settings"):
        op.create_table(
            "user_assistant_settings",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("assistant_persona", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )
    _create_index_if_missing("ix_user_assistant_settings_user_id", "user_assistant_settings", ["user_id"], unique=True)
    _create_index_if_missing("ix_user_assistant_settings_assistant_persona", "user_assistant_settings", ["assistant_persona"])
    _create_index_if_missing("ix_user_assistant_settings_updated_at", "user_assistant_settings", ["updated_at"])

    notification_status = sa.Enum("DRAFT", "PUBLISHED", "ARCHIVED", name="notificationstatus")
    notification_audience = sa.Enum("ALL_USERS", name="notificationaudience")

    if not _has_table("admin_notifications"):
        op.create_table(
            "admin_notifications",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("notification_type", sa.String(), nullable=False),
            sa.Column("status", notification_status, nullable=False),
            sa.Column("audience", notification_audience, nullable=False),
            sa.Column("priority", sa.Integer(), nullable=False),
            sa.Column("action_label", sa.String(), nullable=True),
            sa.Column("action_url", sa.Text(), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by_admin_id", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by_admin_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    for index_name, columns in [
        ("ix_admin_notifications_notification_type", ["notification_type"]),
        ("ix_admin_notifications_status", ["status"]),
        ("ix_admin_notifications_audience", ["audience"]),
        ("ix_admin_notifications_priority", ["priority"]),
        ("ix_admin_notifications_published_at", ["published_at"]),
        ("ix_admin_notifications_expires_at", ["expires_at"]),
        ("ix_admin_notifications_created_at", ["created_at"]),
        ("ix_admin_notifications_updated_at", ["updated_at"]),
    ]:
        _create_index_if_missing(index_name, "admin_notifications", columns)

    if not _has_table("notification_reads"):
        op.create_table(
            "notification_reads",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("notification_id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["notification_id"], ["admin_notifications.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("notification_id", "user_id", name="uq_notification_reads_notification_user"),
        )
    _create_index_if_missing("ix_notification_reads_notification_id", "notification_reads", ["notification_id"])
    _create_index_if_missing("ix_notification_reads_user_id", "notification_reads", ["user_id"])
    _create_index_if_missing("ix_notification_reads_read_at", "notification_reads", ["read_at"])

    admin_notifications = sa.table(
        "admin_notifications",
        sa.column("id", sa.String),
        sa.column("title", sa.String),
        sa.column("summary", sa.Text),
        sa.column("body", sa.Text),
        sa.column("notification_type", sa.String),
        sa.column("status", notification_status),
        sa.column("audience", notification_audience),
        sa.column("priority", sa.Integer),
        sa.column("action_label", sa.String),
        sa.column("action_url", sa.Text),
        sa.column("published_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.utcnow()
    existing = 0
    if not context.is_offline_mode():
        bind = op.get_bind()
        existing = bind.execute(
            sa.select(sa.func.count()).select_from(admin_notifications).where(
                admin_notifications.c.id == "notif_food_recommendation_launch"
            )
        ).scalar_one()
    if context.is_offline_mode() or not existing:
        op.bulk_insert(
            admin_notifications,
            [
                {
                    "id": "notif_food_recommendation_launch",
                    "title": "Ra mắt gợi ý món ăn thông minh",
                    "summary": "AI đã có thể gợi ý món ăn/quán ăn theo vị trí, khẩu vị và ngân sách.",
                    "body": (
                        "Chúng ta vừa bổ sung luồng gợi ý món ăn: AI có thể hỏi vị trí, hiểu khẩu vị, "
                        "lọc theo ngân sách và hiển thị card món/quán để anh/chị chọn nhanh hơn."
                    ),
                    "notification_type": "feature_update",
                    "status": "PUBLISHED",
                    "audience": "ALL_USERS",
                    "priority": 10,
                    "action_label": "Thử gợi ý món ăn",
                    "action_url": "/chat",
                    "published_at": now,
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        )


def downgrade() -> None:
    for table_name in ["notification_reads", "admin_notifications", "user_assistant_settings"]:
        if _has_table(table_name):
            op.drop_table(table_name)
    sa.Enum(name="notificationaudience").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="notificationstatus").drop(op.get_bind(), checkfirst=True)
