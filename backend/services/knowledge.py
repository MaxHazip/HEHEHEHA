"""База знаний: Qdrant-поиск с fallback на keyword-поиск в БД."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.settings import settings
from backend.models import (
    Category,
    KnowledgeArticle,
    Ticket,
    TicketKBArticle,
)

logger = logging.getLogger(__name__)

_qdrant_client: Any = None
_qdrant_checked = False
_indexed = False


def _get_client() -> Any:
    global _qdrant_client, _qdrant_checked

    if _qdrant_checked:
        return _qdrant_client

    _qdrant_checked = True
    if not settings.QDRANT_ENABLED:
        return None

    try:
        from qdrant_client import QdrantClient  # type: ignore
    except ImportError:
        logger.info("qdrant-client не установлен, используется fallback")
        return None

    try:
        kwargs: dict[str, Any] = {
            "url": settings.QDRANT_URL,
            "timeout": 5,
        }
        if settings.QDRANT_API_KEY:
            kwargs["api_key"] = settings.QDRANT_API_KEY
        _qdrant_client = QdrantClient(**kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Qdrant client init failed: %s", exc)
        _qdrant_client = None
    return _qdrant_client


def _reset_client() -> None:
    global _qdrant_client, _qdrant_checked, _indexed
    _qdrant_client = None
    _qdrant_checked = False
    _indexed = False


def _article_text(article: KnowledgeArticle) -> str:
    keywords = " ".join(article.keywords or [])
    return f"{article.title}\n{article.body}\n{keywords}".strip()


async def _embed(text: str) -> list[float] | None:
    if not text.strip():
        return None

    base = (
        settings.EMBEDDING_BASE_URL or settings.OLLAMA_BASE_URL
    ).rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{base}/api/embeddings",
                json={
                    "model": settings.EMBEDDING_MODEL,
                    "prompt": text,
                },
            )
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.info("Embedding unavailable: %s", exc)
        return None

    vector = payload.get("embedding")
    if not isinstance(vector, list) or not vector:
        return None
    try:
        return [float(item) for item in vector]
    except (TypeError, ValueError):
        return None


async def ensure_index(
    session: AsyncSession, *, force: bool = False
) -> int:
    """Индексирует статьи в Qdrant. Возвращает число статей."""

    global _indexed

    if _indexed and not force:
        return 0

    client = _get_client()
    if client is None:
        _indexed = True
        return 0

    articles = (
        await session.scalars(
            select(KnowledgeArticle).order_by(KnowledgeArticle.id)
        )
    ).all()
    if not articles:
        _indexed = True
        return 0

    try:
        from qdrant_client.models import (  # type: ignore
            Distance,
            PointStruct,
            VectorParams,
        )
    except ImportError:
        _indexed = True
        return 0

    try:
        await asyncio.to_thread(client.get_collections)
    except Exception as exc:  # noqa: BLE001
        logger.info("Qdrant unavailable: %s", exc)
        _indexed = True
        return 0

    collection = settings.QDRANT_COLLECTION

    if force:
        try:
            await asyncio.to_thread(client.delete_collection, collection)
        except Exception:  # noqa: BLE001
            pass

    sample = await _embed(_article_text(articles[0]))
    if sample is None:
        _indexed = True
        return 0

    try:
        await asyncio.to_thread(client.get_collection, collection)
    except Exception:  # noqa: BLE001
        await asyncio.to_thread(
            client.create_collection,
            collection_name=collection,
            vectors_config=VectorParams(
                size=len(sample), distance=Distance.COSINE
            ),
        )

    points: list[Any] = []
    for article in articles:
        vector = (
            sample
            if article.id == articles[0].id
            else await _embed(_article_text(article))
        )
        if vector is None:
            continue
        points.append(
            PointStruct(
                id=article.id,
                vector=vector,
                payload={
                    "article_id": article.id,
                    "code": article.code,
                    "title": article.title,
                },
            )
        )

    if points:
        try:
            await asyncio.to_thread(
                client.upsert,
                collection_name=collection,
                points=points,
                wait=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Qdrant upsert failed: %s", exc)
            _indexed = True
            return 0

    _indexed = True
    logger.info("Qdrant: проиндексировано статей: %s", len(points))
    return len(points)


async def _qdrant_search(
    query: str, limit: int
) -> list[tuple[int, float]]:
    client = _get_client()
    if client is None:
        return []

    try:
        await asyncio.to_thread(client.get_collections)
    except Exception:  # noqa: BLE001
        return []

    vector = await _embed(query)
    if vector is None:
        return []

    try:
        if hasattr(client, "query_points"):
            response = await asyncio.to_thread(
                client.query_points,
                collection_name=settings.QDRANT_COLLECTION,
                query=vector,
                limit=limit,
                with_payload=True,
            )
            hits = getattr(response, "points", response)
        else:
            hits = await asyncio.to_thread(
                client.search,
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=vector,
                limit=limit,
                with_payload=True,
            )
    except Exception as exc:  # noqa: BLE001
        logger.info("Qdrant search failed: %s", exc)
        return []

    result: list[tuple[int, float]] = []
    for hit in hits or []:
        payload = getattr(hit, "payload", None) or {}
        article_id = payload.get("article_id")
        score = getattr(hit, "score", 0.0)
        if article_id is None:
            continue
        result.append((int(article_id), float(score or 0.0)))
    return result


def _fallback_search(
    articles: list[KnowledgeArticle], query: str, limit: int
) -> list[tuple[KnowledgeArticle, float]]:
    tokens = {
        token
        for token in re.findall(r"\w+", query.lower())
        if len(token) > 2
    }
    if not tokens:
        return [(article, 0.0) for article in articles[:limit]]

    scored: list[tuple[KnowledgeArticle, float]] = []
    for article in articles:
        haystack = _article_text(article).lower()
        hits = sum(1 for token in tokens if token in haystack)
        if hits:
            scored.append(
                (article, min(1.0, hits / len(tokens)))
            )

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]


async def search_articles(
    session: AsyncSession,
    query: str,
    limit: int | None = None,
) -> list[tuple[KnowledgeArticle, float]]:
    limit = limit or settings.QDRANT_TOP_K
    query = (query or "").strip()

    articles = (
        await session.scalars(
            select(KnowledgeArticle).order_by(KnowledgeArticle.id)
        )
    ).all()

    if not query:
        return [(article, 0.0) for article in articles[:limit]]

    hits = await _qdrant_search(query, limit)
    if hits:
        by_id = {article.id: article for article in articles}
        found: list[tuple[KnowledgeArticle, float]] = []
        seen: set[int] = set()
        for article_id, score in hits:
            article = by_id.get(article_id)
            if article is None or article.id in seen:
                continue
            seen.add(article.id)
            found.append(
                (article, max(0.0, min(1.0, score)))
            )
        if found:
            return found

    return _fallback_search(list(articles), query, limit)


async def recommend_for_ticket(
    session: AsyncSession,
    ticket: Ticket,
    limit: int = 3,
) -> list[tuple[KnowledgeArticle, float]]:
    parts = [ticket.raw_text or ""]
    if ticket.device:
        parts.append(ticket.device)
    if ticket.room:
        parts.append(ticket.room)
    if ticket.building:
        parts.append(ticket.building)
    if ticket.symptoms:
        parts.extend(ticket.symptoms)

    if ticket.category_id:
        category = await session.get(Category, ticket.category_id)
        if category is not None:
            parts.append(category.code)

    query = " ".join(part for part in parts if part).strip()
    results = await search_articles(session, query, limit)

    await session.execute(
        delete(TicketKBArticle).where(
            TicketKBArticle.ticket_id == ticket.id
        )
    )
    for article, score in results[:limit]:
        session.add(
            TicketKBArticle(
                ticket_id=ticket.id,
                article_id=article.id,
                relevance_score=round(max(0.0, min(1.0, score)), 4),
            )
        )
    await session.commit()
    return results


def knowledge_status(article_count: int = 0) -> dict:
    client = _get_client()
    available = False
    if client is not None:
        try:
            client.get_collections()
            available = True
        except Exception:  # noqa: BLE001
            available = False

    return {
        "enabled": settings.QDRANT_ENABLED,
        "qdrant_available": available,
        "indexed": _indexed,
        "collection": settings.QDRANT_COLLECTION,
        "embedding_model": settings.EMBEDDING_MODEL,
        "articles": article_count,
    }


async def reindex(session: AsyncSession) -> int:
    _reset_client()
    return await ensure_index(session, force=True)
