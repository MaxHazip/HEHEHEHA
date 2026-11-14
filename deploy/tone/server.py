"""OpenAI-совместимая HTTP-обёртка над T-one (streaming CTC ASR).

Запускать внутри окружения T-one (или с PYTHONPATH на репозиторий),
потому что используется пакет ``tone``.

Установка:
    git clone https://github.com/voicekit-team/T-one.git
    cd T-one
    uv venv --python 3.11 .venv
    source .venv/bin/activate
    uv pip install -e ".[demo]" python-multipart

Запуск:
    cp /path/to/HEHEHEHA/deploy/tone/server.py .
    OMP_NUM_THREADS=2 uvicorn server:app --host 0.0.0.0 --port 8002
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any

# Ограничиваем ONNX Runtime до импорта tone/onnxruntime.
os.environ.setdefault("OMP_NUM_THREADS", os.getenv("ONNX_NUM_THREADS", "2"))

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from tone import DecoderType, StreamingCTCPipeline, read_audio

logger = logging.getLogger(__name__)
app = FastAPI(title="T-one ASR")

_pipeline: StreamingCTCPipeline | None = None
_pipeline_lock = threading.Lock()
_inference_lock = threading.Lock()


def _decoder_type() -> DecoderType:
    value = os.getenv("TONE_DECODER", "beam").strip().lower()
    return DecoderType.GREEDY if value == "greedy" else DecoderType.BEAM_SEARCH


def get_pipeline() -> StreamingCTCPipeline:
    """Ленивая загрузка pipeline (модель скачивается один раз)."""

    global _pipeline
    with _pipeline_lock:
        if _pipeline is None:
            logger.info("Загружаю T-one с Hugging Face...")
            _pipeline = StreamingCTCPipeline.from_hugging_face(
                decoder_type=_decoder_type()
            )
            logger.info("T-one загружен.")
    return _pipeline


def _to_wav(src: Path, dst: Path) -> Path:
    """Конвертирует любой формат в mono 8 kHz WAV через ffmpeg."""

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        logger.warning("ffmpeg не найден: пробую исходный файл")
        return src

    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(src),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "8000",
            "-sample_fmt",
            "s16",
            "-f",
            "wav",
            str(dst),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        lines = (proc.stderr or "").strip().splitlines()
        raise RuntimeError(f"ffmpeg: {lines[-1] if lines else 'failed'}")
    return dst


def _transcribe(path: Path) -> dict[str, Any]:
    audio = read_audio(path)
    with _inference_lock:
        phrases = get_pipeline().forward_offline(audio)

    segments: list[dict[str, Any]] = []
    for phrase in phrases:
        text = (phrase.text or "").strip()
        if not text:
            continue
        segments.append(
            {
                "start": float(phrase.start_time),
                "end": float(phrase.end_time),
                "text": text,
            }
        )

    return {
        "text": " ".join(item["text"] for item in segments),
        "language": "ru",
        "segments": segments,
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "model": "t-one",
        "sample_rate": 8000,
        "loaded": _pipeline is not None,
    }


@app.post("/audio/transcriptions")
async def transcriptions(
    file: UploadFile = File(...),
    model: str = Form("t-one"),
    language: str = Form("ru"),
    response_format: str = Form("verbose_json"),
) -> JSONResponse:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="Пустой аудиофайл")

    suffix = Path(file.filename or "audio").suffix or ".bin"

    with tempfile.TemporaryDirectory(prefix="tone-") as tmp:
        src = Path(tmp) / f"input{suffix}"
        wav = Path(tmp) / "input.wav"
        src.write_bytes(data)

        try:
            audio_path = await asyncio.to_thread(_to_wav, src, wav)
            result = await asyncio.to_thread(_transcribe, audio_path)
        except ModuleNotFoundError as exc:
            raise HTTPException(
                status_code=503,
                detail="T-one без demo-зависимостей: установите miniaudio.",
            ) from exc
        except Exception as exc:
            logger.exception("T-one transcription failed")
            raise HTTPException(
                status_code=500, detail=f"T-one error: {exc}"
            ) from exc

    return JSONResponse(result)
