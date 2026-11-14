"""Распознавание речи.

Провайдеры:
1. ``tone``   — локальная модель T-one через HTTP-сервер (основной путь);
2. ``http``   — локальный OpenAI-совместимый Whisper-сервер;
3. ``local``  — пакет ``faster-whisper`` прямо в backend-процессе;
4. ``google`` — Google Cloud Speech-to-Text (облачный резерв).

Режим задаётся ``SPEECH_PROVIDER``: ``auto | tone | http | local | google | none``.
T-one не является частью Ollama — это отдельный сервер инференса,
который отдаёт OpenAI-совместимый эндпоинт транскрибации.
"""

import asyncio
import base64
import importlib.util
import logging
import os
import tempfile
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SPEECH_URL = "https://speech.googleapis.com/v1/speech:recognize"

# Google Cloud Speech v1 поддерживает ограниченный набор encoding.
_ENCODING_BY_MIME = {
    "audio/webm": "WEBM_OPUS",
    "audio/ogg": "OGG_OPUS",
    "audio/wav": "LINEAR16",
    "audio/x-wav": "LINEAR16",
    "audio/mpeg": "MP3",
    "audio/mp3": "MP3",
    "audio/flac": "FLAC",
}

_SUFFIX_BY_MIME = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/flac": ".flac",
    "audio/mp4": ".m4a",
}

_MODEL_CACHE: dict[str, Any] = {}
_MODEL_LOCK = asyncio.Lock()


class SpeechProviderError(RuntimeError):
    pass


def _base_mime(mime_type: str | None) -> str:
    return (mime_type or "audio/webm").split(";")[0].strip().lower()


def _short_language(language: str | None) -> str:
    return (language or "ru").split("-")[0].lower()


def _google_key() -> str | None:
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


def _faster_whisper_available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def _provider_sequence(mode: str | None = None) -> list[str]:
    mode = (mode or os.getenv("SPEECH_PROVIDER", "auto")).strip().lower()

    if mode == "none":
        return []
    if mode == "tone":
        return ["tone"]
    if mode == "google":
        return ["google"]
    if mode == "local":
        return ["local"]
    if mode == "http":
        return ["http"]

    # auto (и любое неизвестное значение)
    providers: list[str] = []
    if os.getenv("TONE_BASE_URL"):
        providers.append("tone")
    if os.getenv("WHISPER_BASE_URL"):
        providers.append("http")
    if _faster_whisper_available():
        providers.append("local")
    if _google_key():
        providers.append("google")
    return providers


def speech_status() -> dict:
    """Диагностика для health-эндпоинта и UI."""

    return {
        "mode": os.getenv("SPEECH_PROVIDER", "auto"),
        "tone": bool(os.getenv("TONE_BASE_URL")),
        "local_faster_whisper": _faster_whisper_available(),
        "http_whisper": bool(os.getenv("WHISPER_BASE_URL")),
        "google_stt": bool(_google_key()),
        "providers": _provider_sequence(),
    }


def _normalize_segments(raw: Any) -> list[dict]:
    if not isinstance(raw, list):
        return []

    segments: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        text = str(
            item.get("text") or item.get("transcript") or ""
        ).strip()
        if not text:
            continue

        if item.get("start_ms") is not None:
            start_ms = int(item["start_ms"])
        elif item.get("start") is not None:
            start_ms = int(float(item["start"]) * 1000)
        else:
            start_ms = None

        if item.get("end_ms") is not None:
            end_ms = int(item["end_ms"])
        elif item.get("end") is not None:
            end_ms = int(float(item["end"]) * 1000)
        else:
            end_ms = None

        segments.append(
            {
                "start_ms": start_ms,
                "end_ms": end_ms,
                "text": text,
                "speaker": item.get("speaker"),
                "confidence": item.get("confidence"),
            }
        )
    return segments


async def _transcribe_tone(
    data: bytes,
    mime_type: str,
    language: str,
) -> dict:
    base_url = os.getenv("TONE_BASE_URL")
    if not base_url:
        raise SpeechProviderError("TONE_BASE_URL не задан")

    endpoint = os.getenv("TONE_ENDPOINT", "/audio/transcriptions")
    base_url = base_url.rstrip("/")
    url = base_url if base_url.endswith(endpoint) else f"{base_url}{endpoint}"

    headers: dict[str, str] = {}
    if os.getenv("TONE_API_KEY"):
        headers["Authorization"] = f"Bearer {os.getenv('TONE_API_KEY')}"

    base_mime = _base_mime(mime_type)
    suffix = _SUFFIX_BY_MIME.get(base_mime, ".webm")
    file_field = os.getenv("TONE_FILE_FIELD", "file")

    form = {
        "model": os.getenv("TONE_MODEL", "t-one"),
        "language": os.getenv("TONE_LANGUAGE", "ru"),
        "response_format": "verbose_json",
    }

    timeout = float(os.getenv("TONE_TIMEOUT_SECONDS", "120"))
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                data=form,
                files={file_field: (f"call{suffix}", data, base_mime)},
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("T-one request failed: %s", exc)
        raise SpeechProviderError(
            "Локальный сервер T-one недоступен. Проверьте TONE_BASE_URL."
        ) from exc

    text = payload.get("text") or payload.get("transcription")
    if isinstance(text, dict):
        text = text.get("text")
    if not isinstance(text, str):
        text = ""

    segments = _normalize_segments(payload.get("segments"))
    text = text.strip() or " ".join(s["text"] for s in segments).strip()

    return {
        "text": text,
        "provider": "t-one",
        "language": payload.get("language") or language,
        "segments": segments,
    }


async def _transcribe_google(
    data: bytes,
    mime_type: str,
    language: str,
) -> dict:
    api_key = _google_key()
    if not api_key:
        raise SpeechProviderError("GOOGLE_API_KEY не задан")

    base_mime = _base_mime(mime_type)
    encoding = _ENCODING_BY_MIME.get(base_mime)
    if not encoding:
        raise SpeechProviderError(
            f"Формат {base_mime} не поддерживается Google STT"
        )

    config: dict = {
        "encoding": encoding,
        "languageCode": language,
        "enableAutomaticPunctuation": True,
    }
    if encoding in ("WEBM_OPUS", "OGG_OPUS"):
        config["sampleRateHertz"] = 48000

    body = {
        "config": config,
        "audio": {"content": base64.b64encode(data).decode("ascii")},
    }

    timeout = float(os.getenv("AI_TIMEOUT_SECONDS", "60")) + 20
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                SPEECH_URL,
                params={"key": api_key},
                json=body,
            )
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Google STT request failed: %s", exc)
        raise SpeechProviderError("Сервис Google STT недоступен") from exc

    results = payload.get("results") or []
    texts = [
        alternative.get("transcript", "")
        for result in results
        for alternative in result.get("alternatives", [])[:1]
    ]
    text = " ".join(part.strip() for part in texts if part.strip())

    return {
        "text": text,
        "provider": "google-stt",
        "language": language,
        "segments": [],
    }


async def _transcribe_http(
    data: bytes,
    mime_type: str,
    language: str,
) -> dict:
    base_url = os.getenv("WHISPER_BASE_URL")
    if not base_url:
        raise SpeechProviderError("WHISPER_BASE_URL не задан")

    base_url = base_url.rstrip("/")
    url = (
        base_url
        if base_url.endswith("/audio/transcriptions")
        else f"{base_url}/audio/transcriptions"
    )

    headers: dict[str, str] = {}
    if os.getenv("WHISPER_API_KEY"):
        headers["Authorization"] = f"Bearer {os.getenv('WHISPER_API_KEY')}"

    base_mime = _base_mime(mime_type)
    suffix = _SUFFIX_BY_MIME.get(base_mime, ".webm")

    form = {
        "model": os.getenv(
            "WHISPER_HTTP_MODEL", "Systran/faster-whisper-small"
        ),
        "language": _short_language(language),
        "response_format": "verbose_json",
    }

    try:
        async with httpx.AsyncClient(
            timeout=float(os.getenv("AI_TIMEOUT_SECONDS", "60")) + 60
        ) as client:
            response = await client.post(
                url,
                data=form,
                files={"file": (f"call{suffix}", data, base_mime)},
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Whisper HTTP request failed: %s", exc)
        raise SpeechProviderError(
            "Локальный Whisper-сервер недоступен"
        ) from exc

    return {
        "text": str(payload.get("text", "")).strip(),
        "provider": "whisper-http",
        "language": payload.get("language") or language,
        "segments": _normalize_segments(payload.get("segments")),
    }


def _load_whisper_model() -> tuple[str, Any]:
    # Опциональная зависимость: импортируем динамически, чтобы проект
    # работал и без установленного faster-whisper.
    faster_whisper = importlib.import_module("faster_whisper")
    WhisperModel = faster_whisper.WhisperModel

    name = os.getenv("WHISPER_MODEL", "small")
    device = os.getenv("WHISPER_DEVICE", "auto")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    key = f"{name}:{device}:{compute_type}"

    model = _MODEL_CACHE.get(key)
    if model is None:
        logger.info(
            "Загружаю faster-whisper: model=%s device=%s compute=%s",
            name,
            device,
            compute_type,
        )
        model = WhisperModel(
            name,
            device=device,
            compute_type=compute_type,
        )
        _MODEL_CACHE[key] = model

    return key, model


def _run_local_whisper(
    model: Any,
    key: str,
    data: bytes,
    mime_type: str,
    language: str,
) -> dict:
    base_mime = _base_mime(mime_type)
    suffix = _SUFFIX_BY_MIME.get(base_mime, ".webm")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        path = handle.name

    try:
        segments_iter, info = model.transcribe(
            path,
            language=_short_language(language),
            vad_filter=True,
            beam_size=5,
        )

        segments: list[dict] = []
        texts: list[str] = []
        for segment in segments_iter:
            text = (segment.text or "").strip()
            if not text:
                continue
            texts.append(text)
            segments.append(
                {
                    "start_ms": int(segment.start * 1000),
                    "end_ms": int(segment.end * 1000),
                    "text": text,
                    "speaker": None,
                    "confidence": None,
                }
            )
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    return {
        "text": " ".join(texts).strip(),
        "provider": f"faster-whisper:{key.split(':')[0]}",
        "language": getattr(info, "language", language),
        "segments": segments,
    }


async def _transcribe_local(
    data: bytes,
    mime_type: str,
    language: str,
) -> dict:
    if not _faster_whisper_available():
        raise SpeechProviderError(
            "Пакет faster-whisper не установлен"
        )

    async with _MODEL_LOCK:
        key, model = await asyncio.to_thread(_load_whisper_model)

    return await asyncio.to_thread(
        _run_local_whisper,
        model,
        key,
        data,
        mime_type,
        language,
    )


async def transcribe_audio(
    data: bytes,
    mime_type: str,
    language: str = "ru-RU",
) -> dict:
    """Распознаёт аудио и возвращает ``text`` + ``segments``."""

    providers = _provider_sequence()
    if not providers:
        raise SpeechProviderError(
            "Распознавание речи не настроено. Поднимите сервер T-one и "
            "задайте TONE_BASE_URL, установите faster-whisper, задайте "
            "WHISPER_BASE_URL или GOOGLE_API_KEY."
        )

    handlers = {
        "tone": _transcribe_tone,
        "google": _transcribe_google,
        "http": _transcribe_http,
        "local": _transcribe_local,
    }

    errors: list[str] = []
    for name in providers:
        handler = handlers.get(name)
        if handler is None:
            continue
        try:
            return await handler(data, mime_type, language)
        except SpeechProviderError as exc:
            logger.info("Speech provider %s failed: %s", name, exc)
            errors.append(f"{name}: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected speech provider error (%s)", name)
            errors.append(f"{name}: {type(exc).__name__}")

    raise SpeechProviderError(
        "Не удалось распознать речь. " + " | ".join(errors)
    )
