"""Голосовые ИИ-эндпоинты: T-one (STT), Qwen3 (анализ) и Silero (TTS)."""

import base64
import logging
from typing import Annotated

from fastapi import Depends, APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ai_module.providers.speech_provider import (
    SpeechProviderError,
    speech_status,
    transcribe_audio,
)
from ai_module.providers.tts_provider import (
    TTSProviderError,
    synthesize_speech,
    tts_status,
)
from ai_module.providers.vision_provider import vision_status
from backend.core.settings import settings
from backend.schemas.voice_schemas import (
    TTSRequest,
    TranscriptionResponse,
    VoiceChatResponse,
)
from backend.services.ai_service import analyze_free_text
from backend.services.storage import (
    UploadTooLargeError,
    guess_mime,
    read_upload,
    safe_filename,
)

logger = logging.getLogger(__name__)

from backend.api.access import protect_resources

router = APIRouter(prefix="/api/voice", tags=["voice"], dependencies=[Depends(protect_resources)])


def _reply_for(analysis) -> str:
    """Короткая голосовая реплика по результату анализа."""

    if analysis.intake.questions_to_client:
        return analysis.intake.questions_to_client[0].question
    if analysis.intake.state == "urgent_escalation":
        return (
            "Похоже на серьёзную проблему. Я передал обращение диспетчеру "
            "как срочное."
        )
    return (
        "Спасибо! Обращение принято и передано диспетчеру. "
        "При необходимости он задаст уточняющие вопросы."
    )


@router.get("/status", summary="Состояние локальных голосовых моделей")
async def read_voice_status() -> dict:
    return {
        "speech": speech_status(),
        "tts": tts_status(),
        "vision": vision_status(),
    }


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Распознать речь (T-one / Whisper / Google)",
)
async def transcribe(
    file: Annotated[UploadFile, File(description="Аудиофайл")],
    language: Annotated[str, Form()] = "ru-RU",
) -> TranscriptionResponse:
    try:
        data = await read_upload(file, settings.max_audio_bytes)
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename = safe_filename(file.filename, "audio.webm")
    mime_type = guess_mime(filename, file.content_type)

    try:
        result = await transcribe_audio(data, mime_type, language)
    except SpeechProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return TranscriptionResponse(
        text=str(result.get("text") or ""),
        provider=str(result.get("provider") or "unknown"),
        language=result.get("language") or language,
        segments=list(result.get("segments") or []),
    )


@router.post(
    "/tts",
    summary="Синтезировать речь (Silero TTS)",
)
async def text_to_speech(payload: TTSRequest) -> Response:
    try:
        audio, mime_type = await synthesize_speech(
            payload.text,
            speaker=payload.speaker,
            language=payload.language,
        )
    except TTSProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return Response(
        content=audio,
        media_type=mime_type,
        headers={"Content-Disposition": 'inline; filename="speech.wav"'},
    )


@router.post(
    "/chat",
    response_model=VoiceChatResponse,
    summary="Голосовой цикл: T-one → Qwen3 → Silero TTS",
)
async def voice_chat(
    file: Annotated[UploadFile | None, File(description="Аудио")] = None,
    text: Annotated[str | None, Form()] = None,
    language: Annotated[str, Form()] = "ru-RU",
    speaker: Annotated[str | None, Form()] = None,
) -> VoiceChatResponse:
    """Распознаёт речь, анализирует Qwen3 и озвучивает ответ Silero.

    Можно передать только ``text`` (без аудио) — тогда T-one не нужен.
    Если TTS недоступен, ответ всё равно вернётся (без аудио).
    """

    transcript: str | None = (text or "").strip() or None
    provider: str | None = None

    if file is not None:
        try:
            data = await read_upload(file, settings.max_audio_bytes)
        except UploadTooLargeError as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        filename = safe_filename(file.filename, "audio.webm")
        mime_type = guess_mime(filename, file.content_type)
        try:
            result = await transcribe_audio(data, mime_type, language)
        except SpeechProviderError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        transcript = str(result.get("text") or "").strip() or None
        provider = str(result.get("provider") or "unknown")

    if not transcript:
        raise HTTPException(
            status_code=422,
            detail="Нужен текст или аудио с распознанной речью",
        )

    analysis = await analyze_free_text(transcript)
    reply_text = _reply_for(analysis)

    audio_base64: str | None = None
    audio_mime: str | None = None
    try:
        audio, audio_mime = await synthesize_speech(
            reply_text, speaker=speaker
        )
        audio_base64 = base64.b64encode(audio).decode("ascii")
    except TTSProviderError as exc:
        logger.info("TTS недоступен: %s", exc)

    return VoiceChatResponse(
        transcript=transcript,
        reply_text=reply_text,
        audio_base64=audio_base64,
        audio_mime=audio_mime,
        provider=provider,
    )
