"""Modelos para tutoriales autoguiados por usuario y vista."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.user import User


class UserViewTour(Base):
    """Persistencia del estado de tours por usuario y vista."""

    __tablename__ = "user_view_tours"
    __table_args__ = (
        UniqueConstraint("user_id", "view_key", name="ux_user_view_tours_user_view"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    view_key: Mapped[str] = mapped_column(String(120), index=True)
    tour_version: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    last_step: Mapped[int | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped[User] = relationship(back_populates="view_tours")
