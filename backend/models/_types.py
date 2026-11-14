"""Типы колонок, совместимые с PostgreSQL и SQLite.

Схема БД описана в терминах PostgreSQL: ``BIGINT``, ``TEXT[]``,
``JSONB``, ``TIMESTAMPTZ``. Для локальной разработки и тестов проект
умеет работать на SQLite, поэтому здесь собраны «варианты» типов:

* в PostgreSQL используется нативный тип из ТЗ;
* в SQLite — ближайший эквивалент (``INTEGER``, ``JSON``, ``CHAR(32)``).

Поскольку ``with_variant`` разрешается на этапе компиляции SQL, одни и
те же модели и одна и та же миграция Alembic работают в обеих СУБД.
"""

from sqlalchemy import JSON, BigInteger, Integer, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY, JSONB


def big_int() -> BigInteger:
    """BIGINT в PostgreSQL, INTEGER (для автоинкремента) в SQLite."""

    return BigInteger().with_variant(Integer, "sqlite")


def text_array():
    """TEXT[] в PostgreSQL, JSON-массив строк в SQLite."""

    return ARRAY(Text()).with_variant(JSON(), "sqlite")


def jsonb() -> JSONB:
    """JSONB в PostgreSQL, JSON в SQLite."""

    return JSONB(astext_type=Text()).with_variant(JSON(), "sqlite")


def uuid_pk() -> Uuid:
    """UUID в PostgreSQL, CHAR(32) в SQLite."""

    return Uuid(as_uuid=True)
