"""Вложение к сообщению/заявке.

Файл можно хранить двумя способами:

* ``storage_path`` — путь к файлу в файловом хранилище (продакшен);
* ``data`` — содержимое прямо в БД (демо и перенос окружения без
  отдельного объектного хранилища).

Используется один из них: если ``data`` заполнено, оно имеет приоритет.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base
from backend.models._types import big_int

if TYPE_CHECKING:
    from backend.models.chat_message import ChatMessage
    from backend.models.ticket import Ticket

ATTACHMENT_KINDS = ("image", "audio", "document")


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    __table_args__ = (
        CheckConstraint(
            "kind IN ('image', 'audio', 'document')",
            name="ck_ticket_attachments_kind",
        ),
        CheckConstraint(
            "file_size > 0",
            name="ck_ticket_attachments_file_size",
        ),
        CheckConstraint(
            "length(trim(file_name)) > 0",
            name="ck_ticket_attachments_file_name",
        ),
        CheckConstraint(
            "length(trim(storage_path)) > 0",
            name="ck_ticket_attachments_storage_path",
        ),
        CheckConstraint(
            "length(trim(mime_type)) > 0",
            name="ck_ticket_attachments_mime_type",
        ),
    )

    id: Mapped[int] = mapped_column(big_int(), primary_key=True, autoincrement=True)

    message_id: Mapped[int | None] = mapped_column(
        big_int(),
        ForeignKey("chat_messages.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    ticket_id: Mapped[int | None] = mapped_column(
        big_int(),
        ForeignKey("tickets.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    kind: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="document",
        server_default="document",
    )

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)

    storage_path: Mapped[str] = mapped_column(Text, nullable=False)

    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    file_size: Mapped[int] = mapped_column(big_int(), nullable=False)

    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Результат работы vision-модели (описание изображения).
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Содержимое файла в БД (альтернатива storage_path).
    data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    message: Mapped["ChatMessage | None"] = relationship(
        "ChatMessage",
        back_populates="attachments",
    )

    ticket: Mapped["Ticket | None"] = relationship(
        "Ticket",
        back_populates="attachments",
    )
