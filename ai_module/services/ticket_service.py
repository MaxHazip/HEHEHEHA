"""Фасад ИИ-модуля для backend."""

from ai_module.core.analyzer import get_analyzer
from ai_module.core.schemas import AnalysisRequest, TicketAIResult


async def analyze_ticket(request: AnalysisRequest) -> TicketAIResult:
    """Единая точка входа: текст (и описания вложений) -> результат анализа."""

    return await get_analyzer().analyze(request)
