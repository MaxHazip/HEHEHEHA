"""Совместимая обёртка над новым анализатором.

Раньше здесь планировалась отдельная функция ``analyze_ticket``.
Теперь вся логика живёт в ``ai_module.core.analyzer``, а этот модуль
оставлен для простых вызовов из скриптов и тестов.
"""

import asyncio

from ai_module.core.analyzer import get_analyzer
from ai_module.core.schemas import AnalysisRequest, Message
from ai_module.core.taxonomy import TAXONOMY_VERSION, get_taxonomy


def analyze_ticket(user_text: str) -> dict:
    """Анализирует один текст и возвращает JSON-совместимый dict."""

    if not user_text or not user_text.strip():
        raise ValueError("Текст обращения пустой")

    request = AnalysisRequest(
        ticket_id="legacy",
        source="chat",
        messages=[Message(role="client", text=user_text)],
        taxonomy_version=TAXONOMY_VERSION,
        taxonomy=get_taxonomy(),
    )

    result = asyncio.run(get_analyzer().analyze(request))
    return result.model_dump(mode="json")
