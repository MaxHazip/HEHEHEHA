"""SIP-шлюз.

Backend не поднимает собственный SIP-стек. Вместо этого АТС
(Asterisk/FreeSWITCH/облачная телефония) присылает сюда события:

1. ``POST /api/telephony/sip/calls`` — звонок начался;
2. ``POST /api/telephony/sip/calls/{external_id}/ended`` — звонок завершён,
   можно передать ссылку на запись;
3. ``POST /api/telephony/sip/recording`` — загрузить файл записи напрямую
   (если АТС и backend имеют общий volume или запись отправляет dialplan).

Все эндпоинты защищены заголовком ``X-Telephony-Token``
(значение — ``SIP_WEBHOOK_TOKEN``).
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import Annotated

import httpx
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.serializers import call_read
from backend.core.database import get_session
from backend.core.settings import settings
from backend.models import Call
from backend.schemas.call_schemas import CallDetail, CallRead
from backend.schemas.telephony_schemas import SipCallEnd, SipCallStart
from backend.services.call_service import (
    analyze_call_record,
    build_call_detail,
    find_call_by_external_id,
)
from backend.services.signalling import hub
from backend.services.storage import (
    UploadTooLargeError,
    guess_mime,
    read_upload,
    safe_filename,
)
from backend.services.transcription import (
    store_transcript,
    transcribe_and_store,
)

logger = logging.getLogger(__name__)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def verify_telephony_token(
    x_telephony_token: Annotated[
        str | None, Header(alias="X-Telephony-Token")
    ] = None,
) -> None:
    expected = settings.SIP_WEBHOOK_TOKEN
    if not expected:
        raise HTTPException(
            status_code=503,
            detail=(
                "SIP_WEBHOOK_TOKEN не настроен. Задайте его в .env, "
                "чтобы принимать события от АТС."
            ),
        )
    if not x_telephony_token or not secrets.compare_digest(
        x_telephony_token, expected
    ):
        raise HTTPException(status_code=401, detail="Неверный токен телефонии")


router = APIRouter(
    prefix="/api/telephony",
    tags=["telephony"],
    dependencies=[Depends(verify_telephony_token)],
)

AUDIO_EXTENSIONS = (".wav", ".mp3", ".ogg", ".oga", ".webm", ".m4a", ".mp4")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _finish_call(
    call: Call,
    status_value: str,
    duration_seconds: int | None,
) -> None:
    call.status = status_value
    if call.ended_at is None:
        call.ended_at = _now()

    if duration_seconds is not None:
        call.duration_seconds = duration_seconds
    elif call.duration_seconds is None:
        started = _as_aware(call.started_at)
        ended = _as_aware(call.ended_at)
        if started and ended:
            call.duration_seconds = max(
                0, int((ended - started).total_seconds())
            )


async def _create_call(
    session: AsyncSession, payload: SipCallStart
) -> Call:
    call = Call(
        external_id=payload.external_id,
        direction=payload.direction,
        transport="sip",
        provider=payload.provider,
        client_phone=payload.client_phone or payload.from_number,
        status="active",
        started_at=payload.started_at or _now(),
    )
    session.add(call)
    await session.commit()
    await session.refresh(call)

    await hub.broadcast(
        call.id,
        {
            "type": "status",
            "call_id": call.id,
            "status": call.status,
            "transport": call.transport,
            "external_id": call.external_id,
        },
    )
    return call


async def _download_recording(
    url: str, mime_hint: str | None
) -> tuple[bytes, str]:
    if not url.lower().startswith(("http://", "https://")):
        raise HTTPException(
            status_code=422,
            detail="recording_url должен быть http(s)-ссылкой",
        )

    try:
        async with httpx.AsyncClient(
            timeout=60, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("SIP recording download failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"Не удалось скачать запись звонка: {exc}",
        ) from exc

    data = response.content
    if not data:
        raise HTTPException(status_code=422, detail="Запись пустая")
    if len(data) > settings.max_audio_bytes:
        raise HTTPException(
            status_code=413, detail="Запись превышает MAX_AUDIO_MB"
        )

    mime = (
        mime_hint
        or response.headers.get("content-type")
        or ""
    ).split(";")[0].strip()
    mime = guess_mime(url, mime)
    if not mime.startswith("audio/"):
        raise HTTPException(
            status_code=415, detail="Запись должна быть аудиофайлом"
        )
    return data, mime


async def _save_recording(
    call: Call, data: bytes, mime_type: str
) -> None:
    call.recording_data = data
    call.recording_mime = mime_type
    call.recording_size = len(data)


async def _analyze_sip_call(
    session: AsyncSession, call: Call
) -> None:
    if not settings.SIP_AUTO_ANALYZE:
        return
    if not call.transcript_text and not call.recording_data:
        return
    try:
        await analyze_call_record(session, call)
    except Exception:  # noqa: BLE001
        # Заявка/звонок уже сохранены; сбой анализа не ломает webhook.
        logger.exception("SIP: ИИ-анализ звонка %s не удался", call.id)


@router.post(
    "/sip/calls",
    response_model=CallRead,
    status_code=status.HTTP_201_CREATED,
    summary="SIP: звонок начался",
)
async def sip_call_started(
    payload: SipCallStart, session: SessionDep
) -> CallRead:
    existing = await find_call_by_external_id(
        session, payload.external_id
    )
    if existing is not None:
        return call_read(existing)
    call = await _create_call(session, payload)
    return call_read(call)


@router.get(
    "/sip/calls/{external_id}",
    response_model=CallDetail,
    summary="SIP: состояние звонка по внешнему ID",
)
async def sip_call_detail(
    external_id: str, session: SessionDep
) -> CallDetail:
    call = await find_call_by_external_id(session, external_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Звонок не найден")
    return await build_call_detail(session, call)


@router.post(
    "/sip/calls/{external_id}/ended",
    response_model=CallDetail,
    summary="SIP: звонок завершён",
)
async def sip_call_ended(
    external_id: str,
    payload: SipCallEnd,
    session: SessionDep,
) -> CallDetail:
    call = await find_call_by_external_id(session, external_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Звонок не найден")

    _finish_call(call, payload.status, payload.duration_seconds)

    if payload.recording_url:
        data, mime = await _download_recording(
            payload.recording_url, payload.recording_mime
        )
        await _save_recording(call, data, mime)

    await session.commit()
    await session.refresh(call)

    if call.recording_data is not None and not call.transcript_text:
        await transcribe_and_store(session, call)

    await _analyze_sip_call(session, call)

    await hub.broadcast(
        call.id,
        {
            "type": "status",
            "call_id": call.id,
            "status": call.status,
            "duration_seconds": call.duration_seconds,
            "external_id": call.external_id,
        },
    )
    return await build_call_detail(session, call)


@router.post(
    "/sip/recording",
    response_model=CallDetail,
    status_code=status.HTTP_201_CREATED,
    summary="SIP: загрузить запись звонка",
)
async def sip_upload_recording(
    session: SessionDep,
    file: Annotated[UploadFile, File(description="Аудиозапись звонка")],
    external_id: Annotated[str, Form(min_length=1, max_length=128)],
    transcript: Annotated[str | None, Form()] = None,
    mime_type: Annotated[str | None, Form()] = None,
    from_number: Annotated[str | None, Form()] = None,
    direction: Annotated[str, Form()] = "inbound",
) -> CallDetail:
    call = await find_call_by_external_id(session, external_id)
    if call is None:
        call = Call(
            external_id=external_id,
            direction=direction if direction in ("inbound", "outbound") else "inbound",
            transport="sip",
            provider="asterisk",
            client_phone=from_number,
            status="completed",
            started_at=_now(),
            ended_at=_now(),
        )
        session.add(call)
        await session.flush()

    try:
        data = await read_upload(file, settings.max_audio_bytes)
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename = safe_filename(file.filename, "sip-call.wav")
    resolved_mime = guess_mime(filename, mime_type or file.content_type)
    if not resolved_mime.startswith("audio/") and not filename.lower().endswith(
        AUDIO_EXTENSIONS
    ):
        raise HTTPException(
            status_code=415, detail="Ожидается аудиофайл звонка"
        )

    await _save_recording(call, data, resolved_mime)
    _finish_call(call, "completed", None)

    await session.commit()
    await session.refresh(call)

    if transcript and transcript.strip():
        await store_transcript(
            session,
            call,
            text=transcript,
            provider="sip",
            language=settings.GOOGLE_STT_LANGUAGE,
        )
    else:
        await transcribe_and_store(session, call)

    await _analyze_sip_call(session, call)

    await hub.broadcast(
        call.id,
        {
            "type": "status",
            "call_id": call.id,
            "status": call.status,
            "duration_seconds": call.duration_seconds,
            "external_id": call.external_id,
        },
    )
    return await build_call_detail(session, call)
