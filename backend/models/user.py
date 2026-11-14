"""Пользователь системы (сотрудник компании)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    String,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base
from backend.models._types import big_int

if TYPE_CHECKING:
    from backend.models.chat_session import ChatSession
    from backend.models.engineer import Engineer
    from backend.models.ticket import Ticket
    from backend.models.ticket_event import TicketEvent

USER_ROLES = ("requester", "dispatcher", "engineer")


class User(Base):
    """Сотрудник: заявитель, диспетчер или инженер."""

    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('requester', 'dispatcher', 'engineer')",
            name="ck_users_role",
        ),
        CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_users_name_not_blank",
        ),
        CheckConstraint(
            "length(trim(email)) > 0",
            name="ck_users_email_not_blank",
        ),
        # Уникальность email без учёта регистра.
        Index("uq_users_email_lower", text("lower(email)"), unique=True),
    )

    id: Mapped[int] = mapped_column(big_int(), primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)

    email: Mapped[str] = mapped_column(String(255), nullable=False)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(String(20), nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    engineer: Mapped["Engineer | None"] = relationship(
        "Engineer",
        back_populates="user",
        uselist=False,
    )

    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="creator",
        foreign_keys="Ticket.created_by",
    )

    confirmed_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="confirmer",
        foreign_keys="Ticket.confirmed_by",
    )

    ticket_events: Mapped[list["TicketEvent"]] = relationship(
        "TicketEvent",
        back_populates="actor",
    )
