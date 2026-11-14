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


if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    # Импорт нужен, чтобы все модели попали в Base.metadata.
    from backend import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.run_sync(_apply_light_migrations)


def _apply_light_migrations(sync_connection) -> None:
    """Мини-миграции для уже существующих SQLite/Postgres баз.

    create_all не добавляет новые колонки в существующие таблицы,
    поэтому добавляем их вручную. Для production стоит перейти на Alembic.
    """

    inspector = inspect(sync_connection)
    if "calls" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("calls")}
    if "external_id" not in columns:
        sync_connection.execute(
            text("ALTER TABLE calls ADD COLUMN external_id VARCHAR(128)")
        )

    sync_connection.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_calls_external_id "
            "ON calls (external_id)"
        )
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with create_session_maker() as session:
        yield session
