"""Звонки: WebRTC-сессии, запись, транскрибация и ИИ-анализ."""

import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from ai_module.core.schemas import TicketAIResult
from backend.api.serializers import call_read, call_summary
from backend.core.database import create_session_maker, get_session
from backend.core.settings import settings
from backend.models import Call, Ticket
from backend.schemas.call_schemas import (
    CallCreate,
    CallDetail,
    CallRead,
    CallUpdate,
    TranscriptUpdate,
)
from backend.schemas.ticket_schemas import CallSummary
from backend.services.call_service import (
    analyze_call_record,
    build_call_detail,
)
from backend.services.signalling import hub
from backend.services.storage import (
    UploadTooLargeError,
    file_response,
    guess_mime,
    read_upload,
    safe_filename,
)
from backend.services.transcription import (
    store_transcript,
    transcribe_and_store,
)

router = APIRouter(prefix="/api/calls", tags=["calls"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]

AUDIO_EXTENSIONS = (".webm", ".ogg", ".oga", ".wav", ".mp3", ".m4a", ".mp4")


async def get_call_or_404(session: AsyncSession, call_id: int) -> Call:
    call = await session.get(Call, call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Звонок не найден")
    return call


@router.get(
    "",
    response_model=list[CallSummary],
    summary="Список звонков",
)
async def list_calls(
    session: SessionDep,
    status_filter: str | None = Query(default=None, alias="status"),
    ticket_id: int | None = None,
    phone: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[CallSummary]:
    stmt = select(Call).options(defer(Call.recording_data))

    if status_filter:
        stmt = stmt.where(Call.status == status_filter)
    if ticket_id is not None:
        stmt = stmt.where(Call.ticket_id == ticket_id)
    if phone:
        stmt = stmt.where(Call.client_phone.ilike(f"%{phone}%"))

    stmt = (
        stmt.order_by(Call.created_at.desc())
        .limit(min(limit, 200))
        .offset(offset)
    )
    calls = (await session.scalars(stmt)).all()
    return [call_summary(call) for call in calls]


@router.post(
    "",
    response_model=CallRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать сессию звонка",
)
async def create_call(
    payload: CallCreate, session: SessionDep
) -> CallRead:
    if payload.ticket_id is not None:
        ticket = await session.get(Ticket, payload.ticket_id)
        if ticket is None:
            raise HTTPException(status_code=404, detail="Заявка не найдена")

    call = Call(
        ticket_id=payload.ticket_id,
        direction=payload.direction,
        transport=payload.transport,
        provider=payload.provider,
        client_phone=payload.client_phone,
        status=payload.status,
        started_at=datetime.now(timezone.utc),
    )
    session.add(call)
    await session.commit()
    await session.refresh(call)
    return call_read(call)


@router.get(
    "/{call_id}",
    response_model=CallDetail,
    summary="Звонок с расшифровкой",
)
async def read_call(call_id: int, session: SessionDep) -> CallDetail:
    call = await get_call_or_404(session, call_id)
    return await build_call_detail(session, call)


@router.patch(
    "/{call_id}",
    response_model=CallRead,
    summary="Обновить статус звонка",
)
async def update_call(
    call_id: int,
    payload: CallUpdate,
    session: SessionDep,
) -> CallRead:
    call = await get_call_or_404(session, call_id)
    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(call, field, value)

    if call.status == "completed" and call.ended_at is None:
        call.ended_at = datetime.now(timezone.utc)

    if (
        call.duration_seconds is None
        and call.ended_at is not None
        and call.started_at is not None
    ):
        started_at = call.started_at
        ended_at = call.ended_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        if ended_at.tzinfo is None:
            ended_at = ended_at.replace(tzinfo=timezone.utc)
        delta = ended_at - started_at
        call.duration_seconds = max(0, int(delta.total_seconds()))

    await session.commit()
    await session.refresh(call)

    await hub.broadcast(
        call.id,
        {
            "type": "status",
            "call_id": call.id,
            "status": call.status,
            "duration_seconds": call.duration_seconds,
            "ended_at": (
                call.ended_at.isoformat() if call.ended_at else None
            ),
        },
    )
    return call_read(call)


@router.post(
    "/{call_id}/recording",
    response_model=CallRead,
    summary="Загрузить запись звонка (хранится в БД)",
)
async def upload_recording(
    call_id: int,
    session: SessionDep,
    file: Annotated[UploadFile, File(description="Аудиофайл звонка")],
    mime_type: Annotated[str | None, Form()] = None,
) -> CallRead:
    call = await get_call_or_404(session, call_id)

    try:
        data = await read_upload(file, settings.max_audio_bytes)
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename = safe_filename(file.filename, "call.webm")
    resolved_mime = guess_mime(filename, mime_type or file.content_type)

    if not resolved_mime.startswith("audio/") and not filename.lower().endswith(
        AUDIO_EXTENSIONS
    ):
        raise HTTPException(
            status_code=415, detail="Ожидается аудиофайл звонка"
        )

    call.recording_data = data
    call.recording_mime = resolved_mime
    call.recording_size = len(data)

    await session.commit()
    await session.refresh(call)
    return call_read(call)


@router.get(
    "/{call_id}/recording",
    summary="Прослушать/скачать запись звонка",
)
async def download_recording(
    call_id: int,
    request: Request,
    session: SessionDep,
) -> Response:
    call = await get_call_or_404(session, call_id)
    if call.recording_data is None:
        raise HTTPException(status_code=404, detail="Запись отсутствует")

    filename = f"call-{call.id}"
    if call.recording_mime:
        extension = {
            "audio/webm": ".webm",
            "audio/ogg": ".ogg",
            "audio/wav": ".wav",
            "audio/mpeg": ".mp3",
            "audio/mp4": ".m4a",
        }.get(call.recording_mime.split(";")[0], ".webm")
        filename += extension

    return file_response(
        request,
        call.recording_data,
        call.recording_mime or "audio/webm",
        filename,
    )


@router.put(
    "/{call_id}/transcript",
    response_model=CallDetail,
    summary="Сохранить расшифровку звонка",
)
async def save_transcript(
    call_id: int,
    payload: TranscriptUpdate,
    session: SessionDep,
) -> CallDetail:
    call = await get_call_or_404(session, call_id)

    segments = [segment for segment in payload.segments if segment.text.strip()]
    text = payload.text.strip() or " ".join(
        segment.text.strip() for segment in segments
    )

    await store_transcript(
        session,
        call,
        text=text,
        provider=payload.provider,
        language=payload.language,
        segments=segments,
    )
    return await build_call_detail(session, call)


@router.post(
    "/{call_id}/transcribe",
    response_model=CallDetail,
    summary="Распознать запись на сервере (Google Speech-to-Text)",
)
async def transcribe_recording(
    call_id: int, session: SessionDep
) -> CallDetail:
    call = await get_call_or_404(session, call_id)
    if call.recording_data is None:
        raise HTTPException(status_code=422, detail="Запись отсутствует")

    result, error = await transcribe_and_store(session, call)
    if result is None:
        raise HTTPException(
            status_code=503,
            detail=error
            or (
                "Серверное распознавание недоступно. Установите "
                "faster-whisper, задайте WHISPER_BASE_URL или "
                "GOOGLE_API_KEY."
            ),
        )

    return await build_call_detail(session, call)


@router.post(
    "/{call_id}/analyze",
    response_model=TicketAIResult,
    summary="Проанализировать звонок и обновить заявку",
)
async def analyze_call(
    call_id: int, session: SessionDep
) -> TicketAIResult:
    call = await get_call_or_404(session, call_id)
    return await analyze_call_record(session, call)


@router.get(
    "/{call_id}/transcript",
    response_model=CallDetail,
    summary="Расшифровка звонка",
)
async def read_transcript(
    call_id: int, session: SessionDep
) -> CallDetail:
    call = await get_call_or_404(session, call_id)
    return await build_call_detail(session, call)


@router.websocket("/{call_id}/signal")
async def signal_call(websocket: WebSocket, call_id: int) -> None:
    """WebRTC-сигналинг: обмен offer/answer/ICE и live-расшифровкой."""

    role = websocket.query_params.get("role", "client")
    peer_id = websocket.query_params.get("peer_id")

    async with create_session_maker() as session:
        call = await session.get(Call, call_id)
        if call is None:
            await websocket.close(code=4404)
            return

        snapshot = {
            "status": call.status,
            "external_id": call.external_id,
            "transport": call.transport,
            "provider": call.provider,
            "started_at": (
                call.started_at.isoformat() if call.started_at else None
            ),
            "transcript": call.transcript_text or "",
        }

    await hub.connect(call_id, websocket)
    await websocket.send_json(
        {
            "type": "connected",
            "call_id": call_id,
            "role": role,
            "peer_id": peer_id,
            "peers": hub.peers_count(call_id),
        }
    )
    await websocket.send_json(
        {"type": "snapshot", "call_id": call_id, **snapshot}
    )

    try:
        while True:
            message = await websocket.receive_text()
            # Ограничиваем размер SDP/ICE-сообщений.
            if len(message) > 250_000:
                continue

            payload = None
            try:
                payload = json.loads(message)
            except (TypeError, ValueError):
                payload = None

            if isinstance(payload, dict) and payload.get("type") == "transcript":
                text = str(payload.get("text") or "").strip()
                is_final = bool(payload.get("is_final", False))
                provider = str(
                    payload.get("provider") or "browser-google"
                )

                # Промежуточные результаты не пишем в БД, финальные — да.
                if text and is_final:
                    async with create_session_maker() as store_session:
                        stored = await store_session.get(Call, call_id)
                        if stored is not None:
                            stored.transcript_text = text
                            stored.transcript_language = (
                                stored.transcript_language
                                or settings.GOOGLE_STT_LANGUAGE
                            )
                            stored.transcript_provider = provider
                            await store_session.commit()

                await hub.relay(
                    call_id,
                    websocket,
                    json.dumps(
                        {
                            "type": "transcript",
                            "call_id": call_id,
                            "text": text,
                            "provider": provider,
                            "is_final": is_final,
                        },
                        ensure_ascii=False,
                    ),
                )
                continue

            await hub.relay(call_id, websocket, message)
    except WebSocketDisconnect:
        hub.disconnect(call_id, websocket)
    except Exception:  # noqa: BLE001
        hub.disconnect(call_id, websocket)
