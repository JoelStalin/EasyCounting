"""Modelos para secuencias de comprobantes DGII (NCF/e-CF)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class Sequence(Base):
    """Administración de secuencias de comprobantes por Tenant."""

    __tablename__ = "sequences"
    __table_args__ = (
        UniqueConstraint("tenant_id", "doc_type", name="uq_tenant_doctype_seq"),
    )

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(10), nullable=False)
    prefix: Mapped[str] = mapped_column(String(3), nullable=False)
    next_number: Mapped[int] = mapped_column(Integer, default=1)

    # Relación con Tenant usando string para evitar circularidad
    tenant: Mapped["Tenant"] = relationship(back_populates="sequences")
