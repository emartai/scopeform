from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base

if TYPE_CHECKING:
    from api.models.log import CallLog
    from api.models.organisation import Organisation
    from api.models.token import Token


class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("org_id", "name", name="uq_agents_org_id_name"),
        CheckConstraint(
            "status IN ('active', 'suspended', 'decommissioned')",
            name="ck_agents_status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    owner_email: Mapped[str] = mapped_column(String, nullable=False)
    environment: Mapped[str] = mapped_column(String, nullable=False)
    scopes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active", server_default="active")
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    organisation: Mapped[Organisation] = relationship("Organisation", back_populates="agents")
    tokens: Mapped[list[Token]] = relationship("Token", back_populates="agent")
    call_logs: Mapped[list[CallLog]] = relationship("CallLog", back_populates="agent")

    def __repr__(self) -> str:
        return (
            "Agent("
            f"id={self.id!s}, org_id={self.org_id!s}, name={self.name!r}, "
            f"environment={self.environment!r}, status={self.status!r})"
        )
