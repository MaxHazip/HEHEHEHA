
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.models.chat_message import ChatMessage
    from backend.models.ticket import Ticket


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    __table_args__ = (
        CheckConstraint(
            "file_size > 0",
            name="ck_ticket_attachments_file_size",
        ),
        CheckConstraint(
            "length(btrim(file_name)) > 0",
            name="ck_ticket_attachments_file_name",
        ),
        CheckConstraint(
            "length(btrim(storage_path)) > 0",
            name="ck_ticket_attachments_storage_path",
        ),
        CheckConstraint(
            "length(btrim(mime_type)) > 0",
            name="ck_ticket_attachments_mime_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chat_messages.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    ticket_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tickets.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    message: Mapped["ChatMessage"] = relationship(
        "ChatMessage",
        back_populates="attachments",
    )

    ticket: Mapped["Ticket | None"] = relationship(
        "Ticket",
        back_populates="attachments",
    )
