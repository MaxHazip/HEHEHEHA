"""Создание/поиск пользователей.

Пока в проекте нет авторизации, заявку от анонимного клиента создаёт
служебный пользователь-заявитель. Когда появится вход, сюда достаточно
будет передавать id текущего пользователя.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User

DEFAULT_REQUESTER_PHONE = "+79994567890"
DEFAULT_REQUESTER_NAME = "Заявитель"
DEMO_PASSWORD = "demo-password"


def hash_password(password: str) -> str:
    from pwdlib import PasswordHash

    return PasswordHash.recommended().hash(password)


async def get_user_by_phone(
    session: AsyncSession, phone: str
) -> User | None:
    return await session.scalar(
        select(User).where(User.phone == phone)
    )


async def get_or_create_user(
    session: AsyncSession,
    *,
    phone: str,
    name: str,
    role: str,
    password: str = DEMO_PASSWORD,
) -> User:
    user = await get_user_by_phone(session, phone)
    if user is not None:
        return user

    user = User(
        phone=phone,
        name=name.strip() or phone,
        role=role,
        password_hash=hash_password(password),
    )
    session.add(user)
    await session.flush()
    return user


async def get_or_create_requester(
    session: AsyncSession,
    *,
    phone: str | None = None,
    name: str | None = None,
) -> User:
    """Возвращает заявителя (создаёт служебного при необходимости)."""

    return await get_or_create_user(
        session,
        phone=phone or DEFAULT_REQUESTER_PHONE,
        name=name or DEFAULT_REQUESTER_NAME,
        role="requester",
    )
