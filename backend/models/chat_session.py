from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base 

if TYPE_CHECKING:
    from backend.models.chat_message import ChatMessage
    from backend.models.ticket import Ticket
    from backend.models.user_models import User
    from backend.models.ticket_analysis import TicketAnalysis

import enum


class ChatSessionStatuses(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,          
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[ChatSessionStatuses] = mapped_column(
        Enum(
            ChatSessionStatuses,
            name="chat_session_status_enum",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ChatSessionStatuses.ACTIVE,
        server_default=ChatSessionStatuses.ACTIVE.value,
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