"""История запусков ИИ-анализа по сессии/заявке."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base
from backend.models._types import big_int, jsonb, uuid_pk

if TYPE_CHECKING:
    from backend.models.chat_session import ChatSession
    from backend.models.ticket import Ticket


class TicketAnalysis(Base):
    __tablename__ = "ticket_analyses"

    __table_args__ = (
        UniqueConstraint(
            "chat_session_id",
            "version",
            name="uq_ticket_analyses_session_version",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_ticket_analyses_version",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_ticket_analyses_confidence",
        ),
    )

    id: Mapped[int] = mapped_column(big_int(), primary_key=True, autoincrement=True)

    chat_session_id: Mapped[uuid.UUID] = mapped_column(
        uuid_pk(),
        ForeignKey("chat_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    ticket_id: Mapped[int | None] = mapped_column(
        big_int(),
        ForeignKey("tickets.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )

    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    result: Mapped[dict[str, Any]] = mapped_column(jsonb(), nullable=False)

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    chat_session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="analyses",
    )

    ticket: Mapped["Ticket | None"] = relationship(
        "Ticket",
        back_populates="analyses",
    )
