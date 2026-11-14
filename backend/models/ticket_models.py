from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Ticket(Base):
    """Заявка диспетчерской системы."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    # chat | phone | web
    source: Mapped[str] = mapped_column(String(20), default="chat", index=True)
    # new | in_progress | closed | rejected
    status: Mapped[str] = mapped_column(String(20), default="new", index=True)
    # low | medium | high | critical | needs_review
    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True)

    category_code: Mapped[str] = mapped_column(
        String(64), default="none", index=True
    )
    subcategory_code: Mapped[str] = mapped_column(String(64), default="none")

    client_name: Mapped[str | None] = mapped_column(String(120), default=None)
    client_phone: Mapped[str | None] = mapped_column(String(32), default=None)

    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True
    )

    # Результат работы ИИ.
    ai_description: Mapped[str | None] = mapped_column(Text, default=None)
    ai_solution: Mapped[str | None] = mapped_column(Text, default=None)
    ai_analysis: Mapped[dict | None] = mapped_column(JSON, default=None)
    ai_confidence: Mapped[float | None] = mapped_column(Float, default=None)
    needs_human_review: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class TicketMessage(Base):
    """Сообщение в чате по заявке."""

    __tablename__ = "ticket_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True
    )
    # client | bot | dispatcher | engineer
    role: Mapped[str] = mapped_column(String(20), default="client")
    text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class TicketAttachment(Base):
    """Вложение к заявке.

    Файл хранится прямо в БД (BLOB/BYTEA), чтобы картинки и документы
    не терялись при переносе окружения и были доступны без файлового хранилища.
    """

    __tablename__ = "ticket_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True
    )
    message_id: Mapped[int | None] = mapped_column(
        ForeignKey("ticket_messages.id", ondelete="SET NULL"), default=None, index=True
    )

    # image | audio | document
    kind: Mapped[str] = mapped_column(String(16), default="document")
    filename: Mapped[str] = mapped_column(String(255), default="file")
    mime_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str | None] = mapped_column(String(64), default=None)

    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    # Описание от vision-модели (например, Gemini) или диспетчера.
    description: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class Call(Base):
    """Звонок: запись разговора и транскрибация хранятся в БД."""

    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), default=None, index=True
    )

    # Идентификатор звонка в SIP-АТС (Asterisk/FreeSWITCH/облако).
    external_id: Mapped[str | None] = mapped_column(
        String(128), default=None, index=True
    )

    # inbound | outbound
    direction: Mapped[str] = mapped_column(String(16), default="inbound")
    # webrtc | sip
    transport: Mapped[str] = mapped_column(String(16), default="webrtc")
    provider: Mapped[str | None] = mapped_column(String(64), default=None)
    client_phone: Mapped[str | None] = mapped_column(String(32), default=None)

    # ringing | active | completed | missed | failed
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, default=None)

    # Запись звонка как файл (webm/ogg/wav/mp3).
    recording_mime: Mapped[str | None] = mapped_column(String(128), default=None)
    recording_size: Mapped[int | None] = mapped_column(Integer, default=None)
    recording_data: Mapped[bytes | None] = mapped_column(LargeBinary, default=None)
    # Имя записи в ARI (stored recording) для скачивания из Asterisk.
    recording_name: Mapped[str | None] = mapped_column(
        String(128), default=None, index=True
    )

    # Текстовая расшифровка звонка.
    transcript_text: Mapped[str | None] = mapped_column(Text, default=None)
    transcript_language: Mapped[str | None] = mapped_column(String(16), default=None)
    transcript_provider: Mapped[str | None] = mapped_column(
        String(64), default=None
    )

    ai_analysis: Mapped[dict | None] = mapped_column(JSON, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class CallTranscriptSegment(Base):
    """Таймкодированный фрагмент расшифровки звонка."""

    __tablename__ = "call_transcript_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[int] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    start_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    end_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    speaker: Mapped[str | None] = mapped_column(String(20), default=None)
    text: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float | None] = mapped_column(Float, default=None)


class AIAnalysisRecord(Base):
    """История запусков ИИ-анализа (для воспроизводимости)."""

    __tablename__ = "ai_analysis_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), default=None, index=True
    )
    call_id: Mapped[int | None] = mapped_column(
        ForeignKey("calls.id", ondelete="SET NULL"), default=None, index=True
    )

    schema_version: Mapped[str] = mapped_column(String(16), default="1.0")
    provider: Mapped[str] = mapped_column(String(64), default="rule-based")
    model: Mapped[str | None] = mapped_column(String(64), default=None)
    result: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
