"""Визуальная модель для скриншотов и фото оборудования.

Основной вариант — локальная Qwen3-VL через Ollama. Резерв — Gemini,
если задан ключ. Если не настроено ничего, возвращается ``None``.
"""

import base64
import logging
import os

import httpx

from ai_module.core.prompts import VISION_PROMPT

logger = logging.getLogger(__name__)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}"
    ":generateContent"
)


class VisionProviderError(RuntimeError):
    pass


def vision_status() -> dict:
    return {
        "mode": os.getenv("VISION_PROVIDER", "auto"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL"),
        "ollama_vision_model": os.getenv("OLLAMA_VISION_MODEL"),
        "gemini": bool(
            os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        ),
    }


async def _describe_ollama(
    data: bytes, mime_type: str, model: str, timeout: float
) -> str | None:
    base_url = os.getenv(
        "OLLAMA_BASE_URL", "http://localhost:11434"
    ).rstrip("/")

    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": VISION_PROMPT,
                "images": [base64.b64encode(data).decode("ascii")],
            }
        ],
        "stream": False,
        "think": False,
        "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "2m"),
        "options": {
            "temperature": 0.1,
            # Изображения расходуют контекст быстрее текста;
            # 4096 достаточно для описания скриншота.
            "num_ctx": int(
                os.getenv("OLLAMA_VISION_NUM_CTX", "4096")
            ),
            "num_predict": int(
                os.getenv("OLLAMA_VISION_NUM_PREDICT", "256")
            ),
        },
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(f"{base_url}/api/chat", json=body)
        response.raise_for_status()
        payload = response.json()

    text = str(payload.get("message", {}).get("content", "")).strip()
    return text or None


async def _describe_gemini(
    data: bytes, mime_type: str, model: str, timeout: float
) -> str | None:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(data).decode("ascii"),
                        }
                    },
                    {"text": VISION_PROMPT},
                ],
            }
        ],
        "generationConfig": {"temperature": 0.1},
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            GEMINI_URL.format(model=model),
            params={"key": api_key},
            json=body,
        )
        response.raise_for_status()
        payload = response.json()

    parts = payload["candidates"][0]["content"]["parts"]
    text = "".join(part.get("text", "") for part in parts).strip()
    return text or None


async def describe_image(data: bytes, mime_type: str) -> str | None:
    """Возвращает описание изображения или None, если модель не настроена."""

    mode = os.getenv("VISION_PROVIDER", "auto").strip().lower()
    if mode == "none" or not data:
        return None

    timeout = float(os.getenv("VISION_TIMEOUT_SECONDS", "120"))

    attempts: list[str] = []
    if mode == "ollama":
        attempts = ["ollama"]
    elif mode == "gemini":
        attempts = ["gemini"]
    else:  # auto
        attempts = ["ollama", "gemini"]

    for provider in attempts:
        try:
            if provider == "ollama":
                model = os.getenv(
                    "OLLAMA_VISION_MODEL", "qwen3-vl:2b"
                )
                result = await _describe_ollama(
                    data, mime_type, model, timeout
                )
            else:
                model = (
                    os.getenv("GEMINI_VISION_MODEL")
                    or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                )
                result = await _describe_gemini(
                    data, mime_type, model, timeout
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Vision provider %s failed: %s", provider, exc
            )
            continue

        if result:
            return result

    return None
