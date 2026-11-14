"""Тесты ARI-интеграции без реального Asterisk."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from backend.core.database import Base
from backend.core.settings import settings
from backend.models import Call
from backend.services.ari_service import (
    AriClient,
    build_recording_name,
    handle_ari_event,
)

CHANNEL_ID = "ari-test-1"


class FakeAriClient:
    def __init__(self) -> None:
        self.answered: list[str] = []
        self.recorded: list[tuple[str, str]] = []
        self.played: list[tuple[str, str]] = []

    async def answer(self, channel_id: str) -> None:
        self.answered.append(channel_id)

    async def start_recording(
        self, channel_id: str, name: str
    ) -> None:
        self.recorded.append((channel_id, name))

    async def play(self, channel_id: str, media: str) -> None:
        self.played.append((channel_id, media))

    async def download_recording(self, name: str) -> tuple[bytes, str]:
        assert name == build_recording_name(CHANNEL_ID)
        return b"RIFF-ari-audio", "audio/wav"


def test_ari_events_url(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ARI_WS_URL", None)
    monkeypatch.setattr(settings, "ARI_APP", "dispatchai")

    client = AriClient(
        base_url="http://asterisk:8088",
        username="dispatchai",
        password="secret",
    )
    url = client.events_url()
    assert url.startswith("ws://asterisk:8088/ari/events?")
    assert "app=dispatchai" in url
    assert "subscribeAll=true" in url


def test_ari_recording_flow(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "ARI_RECORD", True)
    monkeypatch.setattr(settings, "ARI_AUTO_ANALYZE", False)
    monkeypatch.setattr(settings, "ARI_GREETING_MEDIA", None)
    monkeypatch.setenv("SPEECH_PROVIDER", "none")

    fake = FakeAriClient()

    async def scenario() -> None:
        db_path = tmp_path / "ari.db"
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}"
        )
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            await handle_ari_event(
                {
                    "type": "StasisStart",
                    "timestamp": "2026-11-14T12:00:00.000+0000",
                    "channel": {
                        "id": CHANNEL_ID,
                        "caller": {"number": "+79995550000"},
                    },
                    "args": [],
                },
                client=fake,
                session_factory=factory,
            )

            await handle_ari_event(
                {
                    "type": "RecordingFinished",
                    "recording": {
                        "name": build_recording_name(CHANNEL_ID),
                        "duration": 12,
                    },
                },
                client=fake,
                session_factory=factory,
            )

            await handle_ari_event(
                {
                    "type": "StasisEnd",
                    "channel": {"id": CHANNEL_ID},
                },
                client=fake,
                session_factory=factory,
            )

            async with factory() as session:
                call = await session.scalar(
                    select(Call).where(Call.external_id == CHANNEL_ID)
                )
                assert call is not None
                assert call.transport == "sip"
                assert call.provider == "asterisk-ari"
                assert call.client_phone == "+79995550000"
                assert call.recording_name == build_recording_name(
                    CHANNEL_ID
                )
                assert call.recording_size == len(b"RIFF-ari-audio")
                assert call.recording_mime == "audio/wav"
                assert call.status == "completed"
                assert call.duration_seconds == 12
                assert call.ticket_id is None
        finally:
            await engine.dispose()

    asyncio.run(scenario())

    assert fake.answered == [CHANNEL_ID]
    assert fake.recorded == [
        (CHANNEL_ID, build_recording_name(CHANNEL_ID))
    ]
