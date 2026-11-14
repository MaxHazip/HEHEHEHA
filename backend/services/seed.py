"""Демо-данные при первом запуске."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.settings import settings
from backend.models import User
from backend.core.security import hash_password

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
    demo_password = settings.DEMO_USER_PASSWORD
    existing_users = (
        await session.scalars(select(User).where(User.phone.in_(phones)))
    ).all()
    by_phone = {user.phone: user for user in existing_users}

    for item in DEMO_USERS:
        if item["phone"] in existing:
            # Пароль демо-учётных записей задаётся только оператором через env.
            current = by_phone.get(item["phone"])
            if current is not None and demo_password and not current.password_hash:
                current.password_hash = hash_password(demo_password)
            continue
        values = dict(item)
        if demo_password:
            values["password_hash"] = hash_password(demo_password)
        session.add(User(**values))
        created += 1

    if created:
        await session.commit()
        logger.info("Создано демо-пользователей: %s", created)
