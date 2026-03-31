"""Shared SQLAlchemy custom types for cross-dialect compatibility."""
from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB as _PGJsonb
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator, TypeEngine


class PortableJSONB(TypeDecorator):
    """
    JSONB for PostgreSQL, JSON for all other dialects (e.g., SQLite in tests).

    This allows models to declare JSONB columns while remaining compatible
    with SQLite-based test databases that use Base.metadata.create_all().

    In production (PostgreSQL), the column is created as JSONB with all its
    indexing and operator benefits. In tests (SQLite), it falls back to JSON.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_PGJsonb())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value
