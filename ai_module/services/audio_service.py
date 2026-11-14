"""Сервисные обёртки над провайдерами."""

import logging

from ai_module.providers.speech_provider import (
    SpeechProviderError,
    transcribe_audio,
)

logger = logging.getLogger(__name__)


async def transcribe_call_recording(
    data: bytes,
    mime_type: str,
    language: str = "ru-RU",
) -> dict | None:
    """Пытается распознать запись на сервере; при ошибке возвращает None."""

    try:
        return await transcribe_audio(data, mime_type, language)
    except SpeechProviderError as exc:
        logger.info("Server-side transcription unavailable: %s", exc)
        return None
