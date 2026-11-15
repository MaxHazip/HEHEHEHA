"""Начальные данные: справочники, демо-пользователи и инженеры."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_module.core.taxonomy import TAXONOMY
from backend.core.settings import settings
from backend.models import (
    Category,
    Engineer,
    KnowledgeArticle,
    Subcategory,
    User,
)
from backend.services.accounts import hash_password

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_FILE = PROJECT_ROOT / "json" / "knowledge_articles.json"

DEMO_USERS: list[dict] = [
    {
        "name": "Иван Диспетчеров",
        "email": "dispatcher@dispatch.local",
        "role": "dispatcher",
        "competencies": [],
    },
    {
        "name": "Иван Сетевой",
        "email": "network@dispatch.local",
        "role": "engineer",
        "competencies": ["network", "wifi", "vpn"],
    },
    {
        "name": "Петр Железнов",
        "email": "hardware@dispatch.local",
        "role": "engineer",
        "competencies": ["hardware", "printer", "power"],
    },
    {
        "name": "Анна Программистова",
        "email": "software@dispatch.local",
        "role": "engineer",
        "competencies": ["software", "access", "mail"],
    },
    {
        "name": "Ольга Телефонистова",
        "email": "phone@dispatch.local",
        "role": "engineer",
        "competencies": ["phone", "access"],
    },
    {
        "name": "Сергей Универсалов",
        "email": "other@dispatch.local",
        "role": "engineer",
        "competencies": ["other"],
    },
    {
        "name": "Заявитель",
        "email": "requester@dispatch.local",
        "role": "requester",
        "competencies": [],
    },
]


async def seed_reference_data(session: AsyncSession) -> None:
    """Дополняет categories/subcategories значениями из справочника ИИ."""

    existing_categories = {
        code
        for code in (
            await session.scalars(select(Category.code))
        ).all()
    }

    categories_by_code: dict[str, Category] = {}
    created = 0

    for item in TAXONOMY:
        category = None
        if item.code in existing_categories:
            category = await session.scalar(
                select(Category).where(Category.code == item.code)
            )
        if category is None:
            category = Category(code=item.code, name=item.name[:100])
            session.add(category)
            await session.flush()
            created += 1
        categories_by_code[item.code] = category

    existing_pairs = {
        (category_id, code)
        for category_id, code in (
            await session.execute(
                select(Subcategory.category_id, Subcategory.code)
            )
        ).all()
    }

    for item in TAXONOMY:
        category = categories_by_code[item.code]
        for sub in item.subcategories:
            if (category.id, sub.code) in existing_pairs:
                continue
            session.add(
                Subcategory(
                    category_id=category.id,
                    code=sub.code,
                    name=sub.name[:100],
                )
            )
            created += 1

    if created:
        await session.commit()
        logger.info("Добавлено записей справочника: %s", created)


async def seed_knowledge(session: AsyncSession) -> None:
    """Загружает статьи базы знаний из json/knowledge_articles.json."""

    if not KNOWLEDGE_FILE.exists():
        return

    try:
        items = json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("Не удалось прочитать %s: %s", KNOWLEDGE_FILE, exc)
        return

    if not isinstance(items, list):
        return

    existing = set(
        (await session.scalars(select(KnowledgeArticle.code))).all()
    )
    created = 0

    for item in items:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "").strip()
        title = str(item.get("title") or "").strip()
        body = str(item.get("body") or "").strip()
        if not code or not title or not body or code in existing:
            continue

        keywords = item.get("keywords") or []
        if not isinstance(keywords, list):
            keywords = []

        session.add(
            KnowledgeArticle(
                code=code,
                title=title[:255],
                body=body,
                keywords=[str(value) for value in keywords],
            )
        )
        existing.add(code)
        created += 1

    if created:
        await session.commit()
        logger.info("Добавлено статей базы знаний: %s", created)


async def seed_demo_data(session: AsyncSession) -> None:
    # Справочники нужны всегда: на них ссылаются заявки и ИИ.
    await seed_reference_data(session)
    await seed_knowledge(session)

    if not settings.SEED_DEMO_DATA:
        return

    password_hash = hash_password("demo-password")
    created = 0

    for item in DEMO_USERS:
        user = await session.scalar(
            select(User).where(User.email == item["email"])
        )
        if user is None:
            user = User(
                name=item["name"],
                email=item["email"],
                role=item["role"],
                password_hash=password_hash,
            )
            session.add(user)
            await session.flush()
            created += 1

        if item["role"] == "engineer":
            engineer = await session.scalar(
                select(Engineer).where(Engineer.user_id == user.id)
            )
            if engineer is None:
                session.add(
                    Engineer(
                        user_id=user.id,
                        competencies=item["competencies"],
                    )
                )
                created += 1
            else:
                merged = sorted(
                    set(engineer.competencies or [])
                    | set(item["competencies"])
                )
                if merged != list(engineer.competencies or []):
                    engineer.competencies = merged
                    created += 1

    if created:
        await session.commit()
        logger.info("Создано демо-записей: %s", created)
