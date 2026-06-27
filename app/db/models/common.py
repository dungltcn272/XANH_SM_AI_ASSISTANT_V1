from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

import pytz
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from app.db.database import Base


def get_vn_time() -> datetime:
    return datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))


def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class NotificationStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class NotificationAudience(str, enum.Enum):
    ALL_USERS = "all_users"
