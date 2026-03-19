"""Modelos de identidad externa y tickets/challenges de autenticacion."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.user import User


class UserExternalIdentity(Base):
    """Identidad de un usuario en un proveedor externo."""

    __tablename__ = "user_external_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_subject", name="ux_user_external_provider_subject"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(30), index=True)
    provider_subject: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    email_verified: Mapped[bool] = mapped_column(default=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped[User] = relationship(back_populates="external_identities")


class AuthLoginChallenge(Base):
    """Challenge de autenticacion de un solo uso para MFA."""

    __tablename__ = "auth_login_challenges"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    portal: Mapped[str] = mapped_column(String(20), index=True)
    provider: Mapped[str] = mapped_column(String(30), default="password")
    challenge_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped[User] = relationship(back_populates="login_challenges")


class AuthLoginTicket(Base):
    """Ticket de un solo uso para intercambiar un login social por la sesion interna."""

    __tablename__ = "auth_login_tickets"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    portal: Mapped[str] = mapped_column(String(20), index=True)
    ticket_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    return_to: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped[User] = relationship(back_populates="login_tickets")
