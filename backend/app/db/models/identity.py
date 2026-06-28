from __future__ import annotations

from .common import *

class Actor(Base):
    __tablename__ = "actors"

    id = Column(String, primary_key=True, default=lambda: generate_id("actor"))
    actor_type = Column(String, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    email = Column(String, nullable=True, unique=True, index=True)
    phone = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)

    @property
    def name(self) -> str | None:
        return self.display_name

    @name.setter
    def name(self, value: str | None) -> None:
        self.display_name = value

    @property
    def role(self) -> UserRole:
        return UserRole.ADMIN if self.actor_type == "admin" else UserRole.USER

    @role.setter
    def role(self, value: UserRole | str) -> None:
        role_value = value.value if isinstance(value, UserRole) else str(value)
        self.actor_type = "admin" if role_value == UserRole.ADMIN.value else "customer"

class ActorIdentity(Base):
    __tablename__ = "actor_identities"
    __table_args__ = (UniqueConstraint("provider", "provider_subject", name="uq_actor_identities_provider_subject"),)

    id = Column(String, primary_key=True, default=lambda: generate_id("identity"))
    actor_id = Column(String, ForeignKey("actors.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)
    provider_subject = Column(String, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class Persona(Base):
    __tablename__ = "personas"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    default_prompt_key = Column(String, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class PersonaAccessGrant(Base):
    __tablename__ = "persona_access_grants"

    id = Column(String, primary_key=True, default=lambda: generate_id("grant"))
    actor_id = Column(String, ForeignKey("actors.id"), nullable=False, index=True)
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    role = Column(String, default="viewer", nullable=False)
    scope_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    expires_at = Column(DateTime(timezone=True), nullable=True)
