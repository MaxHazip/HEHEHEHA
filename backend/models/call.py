"""Звонки: записи разговоров и их расшифровка.

Эти таблицы не входят в «первую группу» из ТЗ (там семь основных
сущностей), но нужны уже реализованной телефонии: WebRTC, SIP и ARI.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base
from backend.models._types import big_int, jsonb


class Call(Base):
    """Звонок: запись разговора и транскрибация хранятся в БД."""

    __tablename__ = "calls"

    created_by: Mapped[int | None] = mapped_column(
        big_int(), ForeignKey("users.id", name="fk_calls_created_by", ondelete="SET NULL")
    )

    id: Mapped[int] = mapped_column(big_int(), primary_key=True, autoincrement=True)

    ticket_id: Mapped[int | None] = mapped_column(
        big_int(),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        default=None,
        index=True,
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
        DateTime(timezone=True), default=func.now()
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
    transcript_provider: Mapped[str | None] = mapped_column(String(64), default=None)

    ai_analysis: Mapped[dict | None] = mapped_column(jsonb(), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), index=True
    )


class CallTranscriptSegment(Base):
    """Таймкодированный фрагмент расшифровки звонка."""

    __tablename__ = "call_transcript_segments"

    id: Mapped[int] = mapped_column(big_int(), primary_key=True, autoincrement=True)

    call_id: Mapped[int] = mapped_column(
        big_int(),
        ForeignKey("calls.id", ondelete="CASCADE"),
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    start_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    end_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    speaker: Mapped[str | None] = mapped_column(String(20), default=None)
    text: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
