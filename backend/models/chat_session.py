"""Сессия общения пользователя с ИИ (существует до создания заявки)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base
from backend.models._types import big_int, uuid_pk

if TYPE_CHECKING:
    from backend.models.chat_message import ChatMessage
    from backend.models.ticket import Ticket
    from backend.models.ticket_analysis import TicketAnalysis
    from backend.models.user import User

CHAT_SESSION_STATUSES = ("active", "completed", "cancelled")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'completed', 'cancelled')",
            name="ck_chat_sessions_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        uuid_pk(),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[int] = mapped_column(
        big_int(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="chat_sessions",
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
        passive_deletes=True,
    )

    ticket: Mapped["Ticket | None"] = relationship(
        "Ticket",
        back_populates="chat_session",
        uselist=False,
    )

    analyses: Mapped[list["TicketAnalysis"]] = relationship(
        "TicketAnalysis",
        back_populates="chat_session",
    )
