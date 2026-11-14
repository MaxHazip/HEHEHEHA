"""Текстовые модели: локальный Qwen3 через Ollama и совместимые API.

Основной вариант — локальная модель Qwen3, поднятая в Ollama. Если она
недоступна, анализатор автоматически откатывается на офлайн-правила,
поэтому демо работает без сети и без платных API.
"""

import logging
import os
from typing import Any, Protocol

import httpx

from ai_module.core.prompts import SYSTEM_PROMPT, build_analysis_prompt
from ai_module.core.schemas import AnalysisRequest
from ai_module.core.validator import extract_json_object

logger = logging.getLogger(__name__)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}"
    ":generateContent"
)


class TextProviderError(RuntimeError):
    """Ошибка текстовой модели. Наружу отдаётся безопасное сообщение."""


class TextProvider(Protocol):
    # Атрибуты намеренно слабо типизированы: у разных провайдеров
    # ``model`` бывает str или None, а Protocol инвариантен.
    name: Any
    model: Any

    async def analyze(self, request: AnalysisRequest) -> dict:
        ...


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class RuleBasedTextProvider:
    """Заглушка-провайдер: анализ выполняет офлайн-анализатор."""

    name = "rule-based"
    model = None

    async def analyze(self, request: AnalysisRequest) -> dict:
        return {}


class GeminiTextProvider:
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def analyze(self, request: AnalysisRequest) -> dict:
        url = GEMINI_URL.format(model=self.model)
        body = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": build_analysis_prompt(request)}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    params={"key": self.api_key},
                    json=body,
                )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini request failed: %s", exc)
            raise TextProviderError("Текстовая модель недоступна") from exc

        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts)
            return extract_json_object(text)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning("Unexpected Gemini response: %s", exc)
            raise TextProviderError(
                "Модель вернула ответ не по контракту"
            ) from exc


class OllamaTextProvider:
    """Локальная модель через Ollama (http://localhost:11434)."""

    name = "ollama"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:4b",
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def analyze(self, request: AnalysisRequest) -> dict:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_analysis_prompt(request),
                },
            ],
            "stream": False,
            "format": "json",
            # Для Qwen3 отключаем «размышления», чтобы получить чистый JSON.
            "think": _env_flag("OLLAMA_THINK", False),
            "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "2m"),
            "options": {
                "temperature": 0.2,
                "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "4096")),
                "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", "768")),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat", json=body
                )
                response.raise_for_status()
                data = response.json()
            content = data["message"]["content"]
            return extract_json_object(content)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Ollama request failed: %s", exc)
            raise TextProviderError(
                "Локальная модель Ollama недоступна. Проверьте, что "
                "Ollama запущена и модель загружена."
            ) from exc


class OpenAICompatibleTextProvider:
    """Любой локальный сервер с OpenAI-совместимым API.

    Подходит LM Studio, llama.cpp server, vLLM, LocalAI и т.п.
    ``OPENAI_BASE_URL`` должен включать ``/v1``.
    """

    name = "openai-compatible"

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    async def analyze(self, request: AnalysisRequest) -> dict:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_analysis_prompt(request),
                },
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=body,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
            content = data["choices"][0]["message"]["content"]
            return extract_json_object(content)
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenAI-compatible request failed: %s", exc)
            raise TextProviderError(
                "Локальный OpenAI-совместимый сервер недоступен. "
                "Проверьте OPENAI_BASE_URL и модель."
            ) from exc


def build_text_provider(provider: str | None = None) -> TextProvider:
    """Выбирает провайдера по настройкам окружения.

    ``AI_PROVIDER``:
    - ``auto`` — локальная Ollama (Qwen3), иначе офлайн-правила;
    - ``ollama`` — локальная Ollama;
    - ``openai`` — локальный OpenAI-совместимый сервер;
    - ``gemini`` — Google Gemini (облако);
    - ``rule`` — только офлайн-анализатор.
    """

    mode = (provider or os.getenv("AI_PROVIDER", "auto")).strip().lower()
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    timeout = float(os.getenv("AI_TIMEOUT_SECONDS", "60"))

    if mode == "ollama":
        return OllamaTextProvider(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "qwen3:4b"),
            timeout=max(timeout, 60.0),
        )

    if mode == "openai":
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("OPENAI_MODEL")
        if base_url and model:
            return OpenAICompatibleTextProvider(
                base_url=base_url,
                model=model,
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=max(timeout, 60.0),
            )
        logger.warning(
            "AI_PROVIDER=openai, но OPENAI_BASE_URL/OPENAI_MODEL не заданы. "
            "Используется офлайн-анализатор."
        )
        return RuleBasedTextProvider()

    if mode == "gemini":
        if api_key:
            return GeminiTextProvider(
                api_key=api_key,
                model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                timeout=timeout,
            )
        logger.warning(
            "AI_PROVIDER=gemini, но GOOGLE_API_KEY не задан. "
            "Используется офлайн-анализатор."
        )
        return RuleBasedTextProvider()

    if mode == "rule":
        return RuleBasedTextProvider()

    # auto: локальная модель приоритетнее облака.
    return OllamaTextProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "qwen3:4b"),
        timeout=max(timeout, 60.0),
    )
