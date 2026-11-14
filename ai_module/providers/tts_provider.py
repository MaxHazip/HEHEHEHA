"""Синтез речи: Silero TTS через локальный HTTP-сервер.

Silero TTS не поддерживается Ollama, поэтому поднимается отдельным
сервисом (см. ``deploy/silero`` и ``docs/local_models.md``). Клиент
ожидает один из форматов ответа:

* ``audio/*`` — тело ответа сразу является аудиофайлом;
* JSON с полем ``audio`` / ``audio_base64`` / ``data`` (base64).
"""

import base64
import logging
import os

import httpx

logger = logging.getLogger(__name__)


class TTSProviderError(RuntimeError):
    pass


def tts_status() -> dict:
    return {
        "provider": os.getenv("TTS_PROVIDER", "silero"),
        "enabled": os.getenv("TTS_ENABLED", "true").strip().lower()
        in ("1", "true", "yes", "on"),
        "silero_url": os.getenv("SILERO_TTS_URL"),
        "speaker": os.getenv("SILERO_SPEAKER", "aidar"),
        "sample_rate": os.getenv("SILERO_SAMPLE_RATE", "48000"),
    }


def _enabled() -> bool:
    provider = os.getenv("TTS_PROVIDER", "silero").strip().lower()
    enabled = os.getenv("TTS_ENABLED", "true").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    return enabled and provider == "silero" and bool(
        os.getenv("SILERO_TTS_URL")
    )


async def synthesize_speech(
    text: str,
    *,
    speaker: str | None = None,
    language: str | None = None,
) -> tuple[bytes, str]:
    """Возвращает ``(audio_bytes, mime_type)``."""

    if not text.strip():
        raise TTSProviderError("Текст для синтеза пустой")
    if not _enabled():
        raise TTSProviderError(
            "Silero TTS не настроен. Поднимите сервер TTS и задайте "
            "SILERO_TTS_URL (и TTS_ENABLED=true)."
        )

    base_url = os.getenv("SILERO_TTS_URL", "").rstrip("/")
    endpoint = os.getenv("SILERO_TTS_ENDPOINT", "/tts")
    url = base_url if base_url.endswith(endpoint) else f"{base_url}{endpoint}"

    payload = {
        "text": text,
        "speaker": speaker or os.getenv("SILERO_SPEAKER", "aidar"),
        "language": language or os.getenv("SILERO_LANGUAGE", "ru"),
        "sample_rate": int(os.getenv("SILERO_SAMPLE_RATE", "48000")),
        "format": "wav",
    }

    timeout = float(os.getenv("SILERO_TIMEOUT_SECONDS", "60"))
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Silero TTS request failed: %s", exc)
        raise TTSProviderError(
            "Сервер Silero TTS недоступен. Проверьте SILERO_TTS_URL."
        ) from exc

    content_type = response.headers.get("content-type", "").split(";")[0]
    if content_type.startswith("audio/"):
        return response.content, content_type

    try:
        data = response.json()
    except ValueError as exc:
        raise TTSProviderError(
            "Сервер TTS вернул не аудио и не JSON"
        ) from exc

    encoded = (
        data.get("audio")
        or data.get("audio_base64")
        or data.get("data")
    )
    if not isinstance(encoded, str) or not encoded:
        raise TTSProviderError("В ответе TTS нет поля с аудио")

    mime_type = data.get("mime_type") or "audio/wav"
    return base64.b64decode(encoded), mime_type
