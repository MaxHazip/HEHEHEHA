"""Локальный HTTP-сервер Silero TTS.

Запуск:
    pip install fastapi "uvicorn[standard]" torch soundfile numpy
    TORCH_NUM_THREADS=2 uvicorn tts_server:app --host 0.0.0.0 --port 8003

Эндпоинт:
    POST /tts  {"text": "...", "speaker": "aidar", "sample_rate": 48000}
    -> audio/wav

Модель скачивается через torch.hub при первом запросе (нужен интернет
один раз), затем работает офлайн.
"""

from __future__ import annotations

import io
import logging
import os

import torch  # type: ignore[import-not-found]
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

app = FastAPI(title="Silero TTS", version="1.0.0")

# Не даём Silero забрать все ядра у Ollama/T-one на CPU-машине.
torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "2")))

_model = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    speaker: str = "aidar"
    language: str = "ru"
    sample_rate: int = 48000


def get_model():
    global _model
    if _model is None:
        logger.info("Загружаю Silero TTS на %s", _device)
        _model, _ = torch.hub.load(
            "snakers4/silero-models",
            "silero_tts",
            language="ru",
            speaker="v3_1_ru",
            trust_repo=True,
        )
        _model.to(_device)
    return _model


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "device": str(_device)}


@app.post("/tts")
def tts(payload: TTSRequest) -> Response:
    try:
        import soundfile as sf  # type: ignore[import-not-found]

        model = get_model()
        audio = model.apply_tts(
            text=payload.text,
            speaker=payload.speaker,
            sample_rate=payload.sample_rate,
        )

        if isinstance(audio, list):
            audio = audio[0]

        buffer = io.BytesIO()
        sf.write(
            buffer,
            audio.detach().cpu().numpy(),
            payload.sample_rate,
            format="WAV",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Silero TTS failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return Response(content=buffer.getvalue(), media_type="audio/wav")
