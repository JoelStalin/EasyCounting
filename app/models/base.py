"""Declaraciones base de SQLAlchemy 2."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column

from app.shared.time import utcnow


class Base(DeclarativeBase):
    """Base para todos los modelos con columnas comunes."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    @declared_attr.directive
    def __tablename__(cls) -> str:  # type: ignore[override]
        return cls.__name__.lower()
