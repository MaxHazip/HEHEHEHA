"""База знаний: список статей, поиск и переиндексация Qdrant."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_session
from backend.models import KnowledgeArticle
from backend.schemas.knowledge_schemas import (
    KnowledgeArticleRead,
    KnowledgeStatus,
)
from backend.services.knowledge import (
    ensure_index,
    knowledge_status,
    reindex,
    search_articles,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _read(article: KnowledgeArticle, score: float | None = None) -> KnowledgeArticleRead:
    return KnowledgeArticleRead(
        id=article.id,
        code=article.code,
        title=article.title,
        body=article.body,
        keywords=list(article.keywords or []),
        score=score,
    )


@router.get(
    "/articles",
    response_model=list[KnowledgeArticleRead],
    summary="Все статьи базы знаний",
)
async def list_articles(
    session: SessionDep,
) -> list[KnowledgeArticleRead]:
    rows = (
        await session.scalars(
            select(KnowledgeArticle).order_by(KnowledgeArticle.id)
        )
    ).all()
    return [_read(article) for article in rows]


@router.get(
    "/search",
    response_model=list[KnowledgeArticleRead],
    summary="Семантический поиск по базе знаний",
)
async def search(
    session: SessionDep,
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(default=5, ge=1, le=20),
) -> list[KnowledgeArticleRead]:
    results = await search_articles(session, q, limit)
    return [_read(article, score) for article, score in results]


@router.get(
    "/status",
    response_model=KnowledgeStatus,
    summary="Состояние Qdrant и индекса",
)
async def status(session: SessionDep) -> KnowledgeStatus:
    count = len(
        (
            await session.scalars(select(KnowledgeArticle.id))
        ).all()
    )
    return KnowledgeStatus(**knowledge_status(count))


@router.post(
    "/reindex",
    response_model=KnowledgeStatus,
    summary="Переиндексировать статьи в Qdrant",
)
async def rebuild_index(session: SessionDep) -> KnowledgeStatus:
    count = len(
        (
            await session.scalars(select(KnowledgeArticle.id))
        ).all()
    )
    await reindex(session)
    return KnowledgeStatus(**knowledge_status(count))
