"""Визуальная модель (Google Gemini) для скриншотов и фото оборудования."""

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


async def describe_image(data: bytes, mime_type: str) -> str | None:
    """Возвращает описание изображения или None, если модель не настроена."""

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("GEMINI_VISION_MODEL") or os.getenv(
        "GEMINI_MODEL", "gemini-2.5-flash"
    )
    timeout = float(os.getenv("AI_TIMEOUT_SECONDS", "20"))

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

    try:
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
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini vision request failed: %s", exc)
        return None
