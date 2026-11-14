import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path


from collections.abc import AsyncGenerator

from sqlalchemy import event, inspect, text

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