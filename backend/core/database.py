from collections.abc import AsyncGenerator

from sqlalchemy import event, inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.core.settings import settings

DATABASE_URL = settings.DATABASE_URL

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


async def init_db() -> None:
    """Создаёт отсутствующие таблицы для локального MVP.

    Для управляемых production-миграций используется Alembic.
    create_all не изменяет уже существующие таблицы.
    """
    # Импорт регистрирует все ORM-модели в Base.metadata.
    import backend.models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
