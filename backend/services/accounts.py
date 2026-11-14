"""Создание/поиск пользователей.

Пока в проекте нет авторизации, заявку от анонимного клиента создаёт
служебный пользователь-заявитель. Когда появится вход, сюда достаточно
будет передавать id текущего пользователя.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User

DEFAULT_REQUESTER_EMAIL = "requester@dispatch.local"
DEFAULT_REQUESTER_NAME = "Заявитель"
DEMO_PASSWORD = "demo-password"


def hash_password(password: str) -> str:
    from pwdlib import PasswordHash

    return PasswordHash.recommended().hash(password)


async def get_user_by_email(
    session: AsyncSession, email: str
) -> User | None:
    return await session.scalar(
        select(User).where(func.lower(User.email) == email.strip().lower())
    )


async def get_or_create_user(
    session: AsyncSession,
    *,
    email: str,
    name: str,
    role: str,
    password: str = DEMO_PASSWORD,
) -> User:
    user = await get_user_by_email(session, email)
    if user is not None:
        return user

    user = User(
        email=email.strip().lower(),
        name=name.strip() or email.split("@")[0],
        role=role,
        password_hash=hash_password(password),
    )
    session.add(user)
    await session.flush()
    return user


async def get_or_create_requester(
    session: AsyncSession,
    *,
    email: str | None = None,
    name: str | None = None,
) -> User:
    """Возвращает заявителя (создаёт служебного при необходимости)."""

    return await get_or_create_user(
        session,
        email=email or DEFAULT_REQUESTER_EMAIL,
        name=name or DEFAULT_REQUESTER_NAME,
        role="requester",
    )
