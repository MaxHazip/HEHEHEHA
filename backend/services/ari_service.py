"""ARI-интеграция с Asterisk.

Backend сам подключается к ARI WebSocket и управляет звонком:

1. ``StasisStart`` — создаёт заявку-звонок, отвечает и включает запись;
2. ``RecordingFinished`` — скачивает WAV из ARI, сохраняет в БД,
   расшифровывает и запускает ИИ-анализ;
3. ``StasisEnd`` / ``ChannelDestroyed`` — завершает звонок и считает
   длительность.

Dialplan в этом режиме содержит только ``Stasis(dispatchai)`` — никаких
``curl`` и ``MixMonitor``.
"""

import asyncio
import json
import logging
import re
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from websockets.asyncio.client import connect as ws_connect

from backend.core.database import create_session_maker
from backend.core.settings import settings
from backend.models import Call
from backend.services.call_service import analyze_call_record
from backend.services.signalling import hub
from backend.services.transcription import transcribe_and_store

logger = logging.getLogger(__name__)

SessionFactory = async_sessionmaker[AsyncSession]


class AriClientError(RuntimeError):
    pass


def build_recording_name(channel_id: str) -> str:
    """Имя stored recording, безопасное для Asterisk."""

    safe = re.sub(r"[^A-Za-z0-9_-]", "_", channel_id)
    return f"dispatchai-{safe}"[:128]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _event_started_at(event: dict) -> datetime:
    raw = event.get("timestamp")
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    return _now()


def _to_seconds(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return max(0, int(float(value)))
    except (TypeError, ValueError):
        return None


class AriClient:
    """Минимальный клиент ARI REST."""

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        base = (base_url or settings.ARI_URL).rstrip("/")
        if not base.endswith("/ari"):
            base = f"{base}/ari"
        self.base_url = base
        self.username = username or settings.ARI_USERNAME
        self.password = password if password is not None else (
            settings.ARI_PASSWORD or ""
        )
        self.timeout = timeout

    def events_url(self) -> str:
        if settings.ARI_WS_URL:
            return settings.ARI_WS_URL

        parsed = urlparse(self.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        credentials = (
            f"{quote(self.username, safe='')}:"
            f"{quote(self.password, safe='')}"
        )
        app = quote(settings.ARI_APP, safe="")
        return (
            f"{scheme}://{parsed.netloc}{parsed.path}/events"
            f"?api_key={credentials}&app={app}&subscribeAll=true"
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        ignore_statuses: tuple[int, ...] = (409,),
        **kwargs: Any,
    ) -> httpx.Response:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=settings.ARI_VERIFY_SSL,
                follow_redirects=True,
            ) as client:
                response = await client.request(
                    method,
                    url,
                    auth=(self.username, self.password),
                    **kwargs,
                )
        except Exception as exc:  # noqa: BLE001
            raise AriClientError(f"ARI {method} {path}: {exc}") from exc

        if (
            response.status_code >= 400
            and response.status_code not in ignore_statuses
        ):
            raise AriClientError(
                f"ARI {method} {path}: {response.status_code} "
                f"{response.text[:200]}"
            )
        return response

    async def answer(self, channel_id: str) -> None:
        await self._request(
            "POST", f"/channels/{quote(channel_id, safe='')}/answer"
        )

    async def start_recording(self, channel_id: str, name: str) -> None:
        await self._request(
            "POST",
            f"/channels/{quote(channel_id, safe='')}/record",
            params={
                "name": name,
                "format": settings.ARI_RECORDING_FORMAT,
                "ifExists": "overwrite",
                "beep": "false",
            },
        )

    async def play(self, channel_id: str, media: str) -> None:
        await self._request(
            "POST",
            f"/channels/{quote(channel_id, safe='')}/play",
            params={"media": media},
            ignore_statuses=(404, 409),
        )

    async def download_recording(self, name: str) -> tuple[bytes, str]:
        response = await self._request(
            "GET",
            f"/recordings/stored/{quote(name, safe='')}/file",
            ignore_statuses=(),
        )
        data = response.content
        if not data:
            raise AriClientError("ARI: пустая запись")

        mime = (
            response.headers.get("content-type") or "audio/wav"
        ).split(";")[0].strip()
        if not mime.startswith("audio/"):
            mime = "audio/wav"
        return data, mime


_client: AriClient | None = None


def get_ari_client() -> AriClient:
    global _client
    if _client is None:
        _client = AriClient()
    return _client


async def _find_by_external_id(
    session: AsyncSession, external_id: str
) -> Call | None:
    return await session.scalar(
        select(Call)
        .where(Call.external_id == external_id)
        .order_by(Call.id.desc())
        .limit(1)
    )


async def _find_by_recording_name(
    session: AsyncSession, name: str
) -> Call | None:
    return await session.scalar(
        select(Call)
        .where(Call.recording_name == name)
        .order_by(Call.id.desc())
        .limit(1)
    )


async def _handle_stasis_start(
    event: dict,
    client: Any,
    session_factory: SessionFactory,
) -> None:
    channel = event.get("channel") or {}
    channel_id = str(channel.get("id") or "").strip()
    if not channel_id:
        return

    caller = channel.get("caller") or {}
    phone = caller.get("number")

    async with session_factory() as session:
        call = await _find_by_external_id(session, channel_id)
        if call is None:
            call = Call(
                external_id=channel_id,
                direction="inbound",
                transport="sip",
                provider="asterisk-ari",
                client_phone=phone,
                status="active",
                started_at=_event_started_at(event),
            )
            session.add(call)
            await session.commit()
            await session.refresh(call)

        call_id = call.id
        recording_name = call.recording_name

    if recording_name is None:
        try:
            await client.answer(channel_id)
        except AriClientError as exc:
            logger.warning("ARI answer %s: %s", channel_id, exc)

        if settings.ARI_GREETING_MEDIA:
            try:
                await client.play(
                    channel_id, settings.ARI_GREETING_MEDIA
                )
            except AriClientError as exc:
                logger.warning("ARI greeting %s: %s", channel_id, exc)

        if settings.ARI_RECORD:
            name = build_recording_name(channel_id)
            try:
                await client.start_recording(channel_id, name)
                async with session_factory() as session:
                    stored = await session.get(Call, call_id)
                    if stored is not None:
                        stored.recording_name = name
                        await session.commit()
            except AriClientError as exc:
                logger.warning("ARI record %s: %s", channel_id, exc)

    await hub.broadcast(
        call_id,
        {
            "type": "status",
            "call_id": call_id,
            "status": "active",
            "transport": "sip",
            "external_id": channel_id,
        },
    )


async def _handle_call_end(
    event: dict, session_factory: SessionFactory
) -> None:
    channel = event.get("channel") or {}
    channel_id = str(channel.get("id") or "").strip()
    if not channel_id:
        return

    call_id: int | None = None
    duration: int | None = None

    async with session_factory() as session:
        call = await _find_by_external_id(session, channel_id)
        if call is None:
            return

        now = _now()
        if call.ended_at is None:
            call.ended_at = now

        started = _as_aware(call.started_at)
        ended = _as_aware(call.ended_at)
        if call.duration_seconds is None and started and ended:
            call.duration_seconds = max(
                0, int((ended - started).total_seconds())
            )
        duration = call.duration_seconds

        if call.status == "active":
            call.status = "completed"

        call_id = call.id
        await session.commit()

    if call_id is not None:
        await hub.broadcast(
            call_id,
            {
                "type": "status",
                "call_id": call_id,
                "status": "completed",
                "duration_seconds": duration,
                "external_id": channel_id,
            },
        )


async def _handle_recording_finished(
    event: dict,
    client: Any,
    session_factory: SessionFactory,
) -> None:
    recording = event.get("recording") or {}
    name = recording.get("name")
    if not isinstance(name, str) or not name:
        return

    async with session_factory() as session:
        call = await _find_by_recording_name(session, name)
        if call is None:
            logger.info("ARI: звонок для записи %s не найден", name)
            return
        if call.recording_size is not None:
            return

        call_id = call.id
        duration = _to_seconds(
            recording.get("duration")
            or recording.get("talking_duration")
        )

    try:
        data, mime = await client.download_recording(name)
    except AriClientError as exc:
        logger.warning("ARI: не удалось скачать запись %s: %s", name, exc)
        return

    async with session_factory() as session:
        call = await session.get(Call, call_id)
        if call is None or call.recording_size is not None:
            return

        call.recording_name = call.recording_name or name
        call.recording_data = data
        call.recording_mime = mime
        call.recording_size = len(data)
        call.status = "completed"
        if call.ended_at is None:
            call.ended_at = _now()

        if duration is not None:
            call.duration_seconds = duration
        elif call.duration_seconds is None and call.started_at:
            started = _as_aware(call.started_at)
            ended = _as_aware(call.ended_at)
            if started and ended:
                call.duration_seconds = max(
                    0, int((ended - started).total_seconds())
                )

        await session.commit()
        await session.refresh(call)

        await transcribe_and_store(session, call)

        if settings.ARI_AUTO_ANALYZE and (
            call.transcript_text or call.recording_data
        ):
            try:
                await analyze_call_record(session, call)
            except Exception:  # noqa: BLE001
                logger.exception(
                    "ARI: ИИ-анализ звонка %s не удался", call.id
                )

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


async def handle_ari_event(
    event: dict,
    *,
    client: Any | None = None,
    session_factory: SessionFactory | None = None,
) -> None:
    """Обрабатывает одно событие ARI (вынесено для тестов)."""

    if not isinstance(event, dict):
        return

    event_type = event.get("type")
    if event_type not in (
        "StasisStart",
        "StasisEnd",
        "ChannelDestroyed",
        "RecordingFinished",
    ):
        return

    ari_client = client or get_ari_client()
    factory = session_factory or create_session_maker

    if event_type == "StasisStart":
        await _handle_stasis_start(event, ari_client, factory)
    elif event_type == "RecordingFinished":
        await _handle_recording_finished(event, ari_client, factory)
    else:
        await _handle_call_end(event, factory)


class AriRunner:
    """Фоновая задача: WebSocket ARI + reconnect."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False
        self.connected = False
        self.last_error: str | None = None
        self.last_event_at: datetime | None = None

    def start(self) -> None:
        if not settings.ARI_ENABLED:
            logger.info("ARI выключен (ARI_ENABLED=false)")
            return
        if not settings.ARI_PASSWORD:
            self.last_error = "ARI_PASSWORD не задан"
            logger.error("ARI включён, но ARI_PASSWORD не задан")
            return
        if self._task is not None and not self._task.done():
            return

        self._running = True
        self._task = asyncio.create_task(self._run(), name="ari-events")
        logger.info(
            "ARI слушает %s, app=%s",
            settings.ARI_URL,
            settings.ARI_APP,
        )

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        self.connected = False

    async def _run(self) -> None:
        client = get_ari_client()

        while self._running:
            try:
                async with ws_connect(
                    client.events_url(),
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=8 * 1024 * 1024,
                ) as socket:
                    self.connected = True
                    self.last_error = None
                    logger.info("ARI подключён")

                    async for raw in socket:
                        if not self._running:
                            break
                        try:
                            event = json.loads(raw)
                        except (TypeError, ValueError):
                            continue

                        self.last_event_at = _now()
                        try:
                            await handle_ari_event(event, client=client)
                        except Exception:  # noqa: BLE001
                            logger.exception(
                                "ARI: ошибка обработки события"
                            )
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                self.connected = False
                # Не сохраняем текст исключения: в URI WebSocket есть api_key.
                self.last_error = type(exc).__name__
                logger.warning(
                    "ARI connection to %s failed: %s",
                    settings.ARI_URL,
                    type(exc).__name__,
                )
                if self._running:
                    await asyncio.sleep(
                        max(settings.ARI_RECONNECT_SECONDS, 1.0)
                    )
            finally:
                self.connected = False

    def status(self) -> dict:
        return {
            "enabled": settings.ARI_ENABLED,
            "running": bool(self._task and not self._task.done()),
            "connected": self.connected,
            "app": settings.ARI_APP,
            "url": settings.ARI_URL,
            "recording": settings.ARI_RECORD,
            "last_error": self.last_error,
            "last_event_at": (
                self.last_event_at.isoformat()
                if self.last_event_at
                else None
            ),
        }


ari_runner = AriRunner()
