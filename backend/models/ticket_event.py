"""События заявки: смена статуса, назначение, подтверждение."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base
from backend.models._types import big_int, jsonb

if TYPE_CHECKING:
    from backend.models.ticket import Ticket
    from backend.models.user import User


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    __table_args__ = (
        CheckConstraint(
            "length(trim(action)) > 0",
            name="ck_ticket_events_action_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(big_int(), primary_key=True, autoincrement=True)

    ticket_id: Mapped[int] = mapped_column(
        big_int(),
        ForeignKey("tickets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    actor_id: Mapped[int | None] = mapped_column(
        big_int(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(String(50), nullable=False)

    field: Mapped[str | None] = mapped_column(String(100), nullable=True)

    old_value: Mapped[Any | None] = mapped_column(jsonb(), nullable=True)

    new_value: Mapped[Any | None] = mapped_column(jsonb(), nullable=True)

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
