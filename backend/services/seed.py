"""Демо-данные при первом запуске."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.settings import settings
from backend.models import User

logger = logging.getLogger(__name__)

DEMO_USERS = [
    {
        "name": "Иван Диспетчеров",
        "phone": "+70000000001",
        "role": "dispatcher",
        "specialty": None,
    },
    {
        "name": "Иван Сетевой",
        "phone": "+70000000002",
        "role": "engineer",
        "specialty": "Сети и интернет",
    },
    {
        "name": "Петр Трубопроводов",
        "phone": "+70000000003",
        "role": "engineer",
        "specialty": "Сантехника",
    },
    {
        "name": "Анна Электрикова",
        "phone": "+70000000004",
        "role": "engineer",
        "specialty": "Электрика",
    },
    {
        "name": "Администратор",
        "phone": "+70000000005",
        "role": "admin",
        "specialty": None,
    },
]


async def seed_demo_data(session: AsyncSession) -> None:
    if not settings.SEED_DEMO_DATA:
        return

    phones = [user["phone"] for user in DEMO_USERS]
    existing = set(
        (
            await session.scalars(
                select(User.phone).where(User.phone.in_(phones))
            )
        ).all()
    )

    created = 0
    for item in DEMO_USERS:
        if item["phone"] in existing:
            continue
        session.add(User(**item))
        created += 1

    if created:
        await session.commit()
        logger.info("Создано демо-пользователей: %s", created)
