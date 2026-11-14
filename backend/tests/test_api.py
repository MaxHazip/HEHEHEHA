"""Интеграционные тесты backend через in-process TestClient."""

import os
import tempfile

import pytest

# Настройки должны быть заданы до импорта приложения.
_TMP_DIR = tempfile.mkdtemp(prefix="dispatchai-tests-")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP_DIR}/test.db"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["AI_PROVIDER"] = "rule"
os.environ["SPEECH_PROVIDER"] = "none"
os.environ["SIP_WEBHOOK_TOKEN"] = "test-telephony-token"
os.environ["ARI_ENABLED"] = "false"
os.environ.pop("GOOGLE_API_KEY", None)
os.environ.pop("GEMINI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"test-image"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_full_ticket_call_flow(client: TestClient) -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert "speech" in health.json()
    assert health.json()["telephony"]["sip_webhook_enabled"] is True

    created = client.post(
        "/api/tickets",
        json={
            "description": (
                "У меня в 305 кабинете не работает интернет. "
                "Перезагрузка не помогла."
            ),
            "source": "chat",
            "client_name": "Тест",
            "client_phone": "+79990000000",
        },
    )
    assert created.status_code == 201, created.text
    ticket = created.json()
    ticket_id = ticket["id"]

    # Автоматический ИИ-анализ при создании заявки.
    assert ticket["category_code"] == "network"
    assert ticket["ai_description"]
    assert ticket["priority"] == "medium"

    # 1. Скриншот сохраняется в БД и отдаётся обратно.
    upload = client.post(
        f"/api/tickets/{ticket_id}/attachments",
        files={"file": ("screen.png", PNG_BYTES, "image/png")},
    )
    assert upload.status_code == 201, upload.text
    attachment = upload.json()
    assert attachment["kind"] == "image"
    assert attachment["size_bytes"] == len(PNG_BYTES)

    content = client.get(attachment["url"])
    assert content.status_code == 200
    assert content.content == PNG_BYTES
    assert content.headers["content-type"].startswith("image/png")

    # 2. Сообщение и повторный анализ (появляется здание).
    message = client.post(
        f"/api/tickets/{ticket_id}/messages",
        json={
            "role": "client",
            "text": "Это второй корпус, проблема у всех в кабинете.",
            "attachment_ids": [attachment["id"]],
        },
    )
    assert message.status_code == 201, message.text
    assert message.json()["attachments"][0]["id"] == attachment["id"]

    analysis = client.post(
        f"/api/tickets/{ticket_id}/analyze", json={"force": True}
    )
    assert analysis.status_code == 200, analysis.text
    result = analysis.json()
    assert result["classification"]["category_code"] == "network"
    assert result["extracted_fields"]["location"]["room"] == "305"
    assert result["extracted_fields"]["location"]["building"] == "2"
    assert "building" not in result["intake"]["missing_fields"]
    assert result["schema_version"] == "1.0"

    cached = client.get(f"/api/ai/tickets/{ticket_id}")
    assert cached.status_code == 200
    assert cached.json()["classification"]["category_code"] == "network"

    # 3. Звонок: запись и расшифровка сохраняются в БД.
    call = client.post(
        "/api/calls",
        json={
            "ticket_id": ticket_id,
            "client_phone": "+79990000000",
            "transport": "webrtc",
        },
    )
    assert call.status_code == 201, call.text
    call_id = call.json()["id"]

    recording = client.post(
        f"/api/calls/{call_id}/recording",
        files={"file": ("call.webm", b"fake-webm-audio", "audio/webm")},
    )
    assert recording.status_code == 200, recording.text
    assert recording.json()["has_recording"] is True
    assert recording.json()["recording_url"] == f"/api/calls/{call_id}/recording"

    # Range-запрос нужен для перемотки аудио.
    ranged = client.get(
        f"/api/calls/{call_id}/recording",
        headers={"Range": "bytes=0-3"},
    )
    assert ranged.status_code == 206
    assert ranged.content == b"fake"
    assert ranged.headers["content-range"] == "bytes 0-3/15"

    # Серверная расшифровка отключена в тестах — endpoint обязан вернуть 503.
    no_speech = client.post(f"/api/calls/{call_id}/transcribe")
    assert no_speech.status_code == 503

    # Завершение звонка без явной длительности: backend считает её сам.
    finished = client.patch(
        f"/api/calls/{call_id}", json={"status": "completed"}
    )
    assert finished.status_code == 200, finished.text
    assert finished.json()["duration_seconds"] is not None

    transcript = client.put(
        f"/api/calls/{call_id}/transcript",
        json={
            "text": (
                "У меня не работает интернет в 305 кабинете, "
                "перезагрузка не помогла"
            ),
            "provider": "browser-google",
            "segments": [
                {"start_ms": 0, "end_ms": 3000, "text": "Не работает интернет"},
                {"start_ms": 3000, "end_ms": 6000, "text": "В 305 кабинете"},
            ],
        },
    )
    assert transcript.status_code == 200, transcript.text
    detail = transcript.json()
    assert len(detail["segments"]) == 2
    assert detail["transcript_provider"] == "browser-google"

    # 4. Анализ звонка обновляет заявку.
    call_analysis = client.post(f"/api/calls/{call_id}/analyze")
    assert call_analysis.status_code == 200, call_analysis.text
    assert call_analysis.json()["ticket_id"] == str(ticket_id)

    # 5. Всё это видно в карточке заявки.
    ticket_detail = client.get(f"/api/tickets/{ticket_id}")
    assert ticket_detail.status_code == 200
    payload = ticket_detail.json()
    assert len(payload["attachments"]) == 1
    assert len(payload["calls"]) == 1
    assert payload["calls"][0]["has_recording"] is True
    assert payload["messages"]

    listing = client.get("/api/tickets")
    assert listing.status_code == 200
    assert any(item["id"] == ticket_id for item in listing.json())

    taxonomy = client.get("/api/ai/taxonomy")
    assert taxonomy.status_code == 200
    assert taxonomy.json()["version"]
    assert taxonomy.json()["categories"]


def test_sip_webhook_flow(client: TestClient) -> None:
    headers = {"X-Telephony-Token": "test-telephony-token"}

    unauthorized = client.post(
        "/api/telephony/sip/calls", json={"external_id": "sip-401"}
    )
    assert unauthorized.status_code == 401

    started = client.post(
        "/api/telephony/sip/calls",
        headers=headers,
        json={
            "external_id": "sip-test-1",
            "from_number": "+79995550000",
            "provider": "asterisk",
        },
    )
    assert started.status_code == 201, started.text
    assert started.json()["transport"] == "sip"

    uploaded = client.post(
        "/api/telephony/sip/recording",
        headers=headers,
        data={
            "external_id": "sip-test-1",
            "transcript": "Не работает интернет в 305 кабинете",
        },
        files={
            "file": ("sip-call.wav", b"RIFF-test-audio", "audio/wav")
        },
    )
    assert uploaded.status_code == 201, uploaded.text
    detail = uploaded.json()
    assert detail["has_recording"] is True
    assert detail["transcript_text"] == "Не работает интернет в 305 кабинете"
    assert detail["ticket_id"] is not None

    by_external = client.get(
        "/api/telephony/sip/calls/sip-test-1", headers=headers
    )
    assert by_external.status_code == 200

    listing = client.get("/api/calls")
    assert listing.status_code == 200
    assert any(
        item["external_id"] == "sip-test-1" for item in listing.json()
    )


def test_websocket_live_transcript(client: TestClient) -> None:
    created = client.post(
        "/api/calls", json={"client_phone": "+79991112233"}
    )
    assert created.status_code == 201, created.text
    call_id = created.json()["id"]

    with client.websocket_connect(

        f"/api/calls/{call_id}/signal?role=client"

    ) as ws_client:
        assert ws_client.receive_json()["type"] == "connected"
        assert ws_client.receive_json()["type"] == "snapshot"

        with client.websocket_connect(

            f"/api/calls/{call_id}/signal?role=dispatcher"

        ) as ws_dispatcher:
            assert ws_dispatcher.receive_json()["type"] == "connected"
            assert ws_dispatcher.receive_json()["type"] == "snapshot"

            ws_client.send_json(
                {
                    "type": "transcript",
                    "text": "Проверка live-субтитров",
                    "is_final": True,
                    "provider": "browser-google",
                }
            )
            event = ws_dispatcher.receive_json()
            assert event["type"] == "transcript"
            assert event["text"] == "Проверка live-субтитров"

    detail = client.get(f"/api/calls/{call_id}")
    assert detail.status_code == 200
    assert detail.json()["transcript_text"] == "Проверка live-субтитров"
