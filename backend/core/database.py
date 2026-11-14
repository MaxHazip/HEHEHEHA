"""Подключение к БД и управление схемой.

Схема БД создаётся и обновляется **только** через Alembic
(``alembic upgrade head``). Приложение не вызывает ``create_all`` —
это гарантирует, что локальная и продакшен-БД совпадают с миграциями.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.core.settings import settings

logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL

PROJECT_ROOT = Path(__file__).resolve().parents[2]

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

create_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with create_session_maker() as session:
        yield session


def _alembic_config():
    """Собирает конфиг Alembic с абсолютными путями.

    Нужен для запуска миграций из приложения независимо от текущей
    рабочей директории.
    """

    from alembic.config import Config

    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", settings.alembic_database_url)
    return config


def _upgrade_to_head() -> None:
    from alembic import command

    command.upgrade(_alembic_config(), "head")


async def init_db() -> None:
    """Применяет миграции Alembic до последней ревизии."""

    logger.info("Применяю миграции Alembic...")
    await asyncio.to_thread(_upgrade_to_head)
    logger.info("Схема БД готова.")
