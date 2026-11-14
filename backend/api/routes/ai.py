"""ИИ-эндпоинты: справочник, предпросмотр анализа, результат по заявке."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ai_module.core.schemas import TicketAIResult
from ai_module.core.taxonomy import (
    ATTEMPTED_ACTIONS,
    SYMPTOMS,
    TAXONOMY_VERSION,
    get_taxonomy,
)
from backend.core.database import get_session
from backend.models import Ticket
from backend.schemas.ai_schemas import AnalyzeTextRequest
from backend.services.ai_service import (
    analysis_result,
    analyze_free_text,
    latest_analysis,
)

from backend.api.access import protect_resources

router = APIRouter(prefix="/api/ai", tags=["ai"], dependencies=[Depends(protect_resources)])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/taxonomy", summary="Справочник категорий и кодов")
async def read_taxonomy() -> dict:
    return {
        "version": TAXONOMY_VERSION,
        "categories": [
            category.model_dump(mode="json") for category in get_taxonomy()
        ],
        "symptoms": SYMPTOMS,
        "attempted_actions": ATTEMPTED_ACTIONS,
    }


@router.post(
    "/analyze-text",
    response_model=TicketAIResult,
    summary="Анализ текста без создания заявки",
)
async def analyze_text(payload: AnalyzeTextRequest) -> TicketAIResult:
    return await analyze_free_text(payload.text, payload.source)


@router.get(
    "/tickets/{ticket_id}",
    summary="Сохранённый результат анализа заявки",
)
async def read_ticket_analysis(
    ticket_id: int, session: SessionDep
) -> dict:
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    analysis = await latest_analysis(session, ticket)
    result = analysis_result(analysis)
    if result is None:
        raise HTTPException(
            status_code=404, detail="Анализ для заявки ещё не выполнялся"
        )
    return result.model_dump(mode="json")
