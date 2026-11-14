"""Расшифровка звонков и сохранение сегментов."""

import logging
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from ai_module.providers.speech_provider import (
    SpeechProviderError,
    transcribe_audio,
)
from backend.core.settings import settings
from backend.models import Call, CallTranscriptSegment
from backend.services.signalling import hub

logger = logging.getLogger(__name__)


def _get(segment: Any, key: str, default: Any = None) -> Any:
    if isinstance(segment, dict):
        return segment.get(key, default)
    return getattr(segment, key, default)


async def store_transcript(
    session: AsyncSession,
    call: Call,
    *,
    text: str,
    provider: str,
    language: str | None = None,
    segments: list[Any] | None = None,
) -> None:
    """Сохраняет текст и таймкоды, затем рассылает live-обновление."""

    clean_text = (text or "").strip()
    clean_segments = [
        segment
        for segment in (segments or [])
        if str(_get(segment, "text", "")).strip()
    ]

    call.transcript_text = clean_text or None
    call.transcript_language = language or settings.GOOGLE_STT_LANGUAGE
    call.transcript_provider = provider

    await session.execute(
        delete(CallTranscriptSegment).where(
            CallTranscriptSegment.call_id == call.id
        )
    )

    for index, segment in enumerate(clean_segments):
        session.add(
            CallTranscriptSegment(
                call_id=call.id,
                position=index,
                start_ms=_get(segment, "start_ms"),
                end_ms=_get(segment, "end_ms"),
                speaker=_get(segment, "speaker"),
                text=str(_get(segment, "text", "")).strip(),
                confidence=_get(segment, "confidence"),
            )
        )

    await session.commit()
    await session.refresh(call)

    await hub.broadcast(
        call.id,
        {
            "type": "transcript",
            "call_id": call.id,
            "text": clean_text,
            "provider": provider,
            "language": call.transcript_language,
            "is_final": True,
            "segments": [
                {
                    "start_ms": _get(segment, "start_ms"),
                    "end_ms": _get(segment, "end_ms"),
                    "text": str(_get(segment, "text", "")).strip(),
                }
                for segment in clean_segments
            ],
        },
    )


async def transcribe_and_store(
    session: AsyncSession,
    call: Call,
    language: str | None = None,
) -> tuple[dict | None, str | None]:
    """Пробует локальный/HTTP/Google STT и сохраняет результат.

    Возвращает ``(result, error)``. Ошибка не выбрасывается, чтобы
    вызывающий код мог решить, делать ли 503 или продолжать без текста.
    """

    if call.recording_data is None:
        return None, "Запись звонка отсутствует"

    try:
        result = await transcribe_audio(
            call.recording_data,
            call.recording_mime or "audio/webm",
            language or settings.GOOGLE_STT_LANGUAGE,
        )
    except SpeechProviderError as exc:
        logger.warning("Транскрибация звонка %s не удалась: %s", call.id, exc)
        return None, str(exc)

    await store_transcript(
        session,
        call,
        text=str(result.get("text", "")),
        provider=str(result.get("provider") or "unknown"),
        language=str(result.get("language") or language or ""),
        segments=result.get("segments") or [],
    )
    return result, None
