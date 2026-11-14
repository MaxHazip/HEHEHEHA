
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.models.ticket import Ticket
    from backend.models.user_models import User


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    __table_args__ = (
        CheckConstraint(
            "length(btrim(action)) > 0",
            name="ck_ticket_events_action_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    ticket_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tickets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    actor_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    field: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    old_value: Mapped[Any | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    new_value: Mapped[Any | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    ticket: Mapped["Ticket"] = relationship(
        "Ticket",
        back_populates="events",
    )

    actor: Mapped["User | None"] = relationship(
        "User",
        back_populates="ticket_events",
    )
