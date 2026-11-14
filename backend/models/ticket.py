"""Главная модель приложения — заявка."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base
from backend.models._types import big_int, text_array, uuid_pk

if TYPE_CHECKING:
    from backend.models.category import Category
    from backend.models.chat_session import ChatSession
    from backend.models.engineer import Engineer
    from backend.models.subcategory import Subcategory
    from backend.models.ticket_analysis import TicketAnalysis
    from backend.models.ticket_attachment import TicketAttachment
    from backend.models.ticket_event import TicketEvent
    from backend.models.ticket_kb_article_models import TicketKBArticle
    from backend.models.user import User

TICKET_STATUSES = ("draft", "new", "in_progress", "resolved", "closed")
TICKET_PRIORITIES = ("low", "medium", "high", "critical")
TICKET_CHANNELS = ("chat", "voice", "image")


class Ticket(Base):
    __tablename__ = "tickets"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'new', 'in_progress', 'resolved', 'closed')",
            name="ck_tickets_status",
        ),
        CheckConstraint(
            "priority IS NULL OR priority IN ('low', 'medium', 'high', 'critical')",
            name="ck_tickets_priority",
        ),
        CheckConstraint(
            "channel IN ('chat', 'voice', 'image')",
            name="ck_tickets_channel",
        ),
        CheckConstraint(
            "length(trim(raw_text)) > 0",
            name="ck_tickets_raw_text_not_blank",
        ),
        Index("ix_tickets_created_by", "created_by"),
        Index("ix_tickets_engineer_id", "engineer_id"),
        Index("ix_tickets_status", "status"),
    )

    id: Mapped[int] = mapped_column(big_int(), primary_key=True, autoincrement=True)

    chat_session_id: Mapped[uuid.UUID] = mapped_column(
        uuid_pk(),
        ForeignKey("chat_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    created_by: Mapped[int] = mapped_column(
        big_int(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    reviewed_description: Mapped[str | None] = mapped_column(Text)

    channel: Mapped[str] = mapped_column(String(20), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    category_id: Mapped[int | None] = mapped_column(
        big_int(),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
    )

    subcategory_id: Mapped[int | None] = mapped_column(
        big_int(),
        ForeignKey("subcategories.id", ondelete="RESTRICT"),
        nullable=True,
    )

    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)

    device: Mapped[str | None] = mapped_column(String(100), nullable=True)
    building: Mapped[str | None] = mapped_column(String(100), nullable=True)
    floor: Mapped[str | None] = mapped_column(String(30), nullable=True)
    room: Mapped[str | None] = mapped_column(String(50), nullable=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)

    symptoms: Mapped[list[str]] = mapped_column(
        text_array(),
        nullable=False,
        default=list,
    )
    attempted_actions: Mapped[list[str]] = mapped_column(
        text_array(),
        nullable=False,
        default=list,
    )
    missing_fields: Mapped[list[str]] = mapped_column(
        text_array(),
        nullable=False,
        default=list,
    )

    is_mass_incident: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    needs_human_review: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    recommended_engineer_id: Mapped[int | None] = mapped_column(
        big_int(),
        ForeignKey("engineers.id", ondelete="SET NULL"),
        nullable=True,
    )
    engineer_id: Mapped[int | None] = mapped_column(
        big_int(),
        ForeignKey("engineers.id", ondelete="SET NULL"),
        nullable=True,
    )

    confirmed_by: Mapped[int | None] = mapped_column(
        big_int(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    chat_session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="ticket",
    )
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="tickets",
    )
    confirmer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[confirmed_by],
        back_populates="confirmed_tickets",
    )
    category: Mapped["Category | None"] = relationship(
        "Category",
        back_populates="tickets",
    )
    subcategory: Mapped["Subcategory | None"] = relationship(
        "Subcategory",
        back_populates="tickets",
    )
    engineer: Mapped["Engineer | None"] = relationship(
        "Engineer",
        foreign_keys=[engineer_id],
        back_populates="assigned_tickets",
    )
    recommended_engineer: Mapped["Engineer | None"] = relationship(
        "Engineer",
        foreign_keys=[recommended_engineer_id],
        back_populates="recommended_tickets",
    )

    analyses: Mapped[list["TicketAnalysis"]] = relationship(
        "TicketAnalysis",
        back_populates="ticket",
    )
    events: Mapped[list["TicketEvent"]] = relationship(
        "TicketEvent",
        back_populates="ticket",
        order_by="TicketEvent.created_at",
    )
    kb_recommendations: Mapped[list["TicketKBArticle"]] = relationship(
        "TicketKBArticle",
        back_populates="ticket",
    )
    attachments: Mapped[list["TicketAttachment"]] = relationship(
        "TicketAttachment",
        back_populates="ticket",
    )
