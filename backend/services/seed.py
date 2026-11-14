"""Начальные данные: справочники, демо-пользователи и инженеры.

Справочники намеренно добавляются здесь, а не в объявлении моделей:
схема живёт в Alembic, а данные — в сервисе инициализации.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_module.core.taxonomy import TAXONOMY
from backend.core.settings import settings
from backend.models import Category, Engineer, Subcategory, User
from backend.services.accounts import hash_password

logger = logging.getLogger(__name__)

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


async def seed_demo_data(session: AsyncSession) -> None:
    # Справочники нужны всегда: на них ссылаются заявки и ИИ.
    await seed_reference_data(session)

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

    if created:
        await session.commit()
        logger.info("Создано демо-записей: %s", created)
