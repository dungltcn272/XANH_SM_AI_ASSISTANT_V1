from __future__ import annotations

from .common import *

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: generate_id("pay"))
    actor_id = Column(String, ForeignKey("actors.id"), nullable=True, index=True)
    trip_id = Column(String, ForeignKey("trips.id"), nullable=True, index=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String, default="VND", nullable=False)
    method = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    provider_ref = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: generate_id("notif"))
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    audience_type = Column(String, nullable=False, index=True)
    audience_json = Column(Text, nullable=True)
    status = Column(String, default="draft", nullable=False, index=True)
    created_by_actor_id = Column(String, ForeignKey("actors.id"), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

    @property
    def summary(self) -> str | None:
        return None

    @property
    def notification_type(self) -> str:
        return "announcement"

    @property
    def audience(self) -> NotificationAudience:
        return NotificationAudience.ALL_USERS

    @property
    def priority(self) -> int:
        return 100

    @property
    def action_label(self) -> str | None:
        return None

    @property
    def action_url(self) -> str | None:
        return None

class NotificationRead(Base):
    __tablename__ = "notification_reads"
    __table_args__ = (UniqueConstraint("notification_id", "actor_id", name="uq_notification_reads_notification_actor"),)

    id = Column(String, primary_key=True, default=lambda: generate_id("notifread"))
    notification_id = Column(String, ForeignKey("notifications.id"), nullable=False, index=True)
    actor_id = Column(String, ForeignKey("actors.id"), nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), default=get_vn_time, index=True)

    @property
    def user_id(self) -> str:
        return self.actor_id

    @user_id.setter
    def user_id(self, value: str) -> None:
        self.actor_id = value

class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(String, primary_key=True, default=lambda: generate_id("feedback"))
    run_id = Column(String, ForeignKey("assistant_runs.id"), nullable=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True, index=True)
    actor_id = Column(String, ForeignKey("actors.id"), nullable=True, index=True)
    rating = Column(String, nullable=False)
    reason_tags_json = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    status = Column(String, default="new", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

    @property
    def reason_tags(self) -> str | None:
        return self.reason_tags_json

    @reason_tags.setter
    def reason_tags(self, value: str | None) -> None:
        self.reason_tags_json = value

    @property
    def admin_note(self) -> str | None:
        return None
