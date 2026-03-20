"""Modelos para secuencias de comprobantes DGII (NCF/e-CF)."""
from __future__ import annotations

from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Sequence(Base):
    """Secuencias de comprobantes por tipo y empresa."""

    __tablename__ = "sequences"

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(10), nullable=False)  # '31', '32', '33' etc.
    prefix: Mapped[str] = mapped_column(String(3), nullable=False)     # 'E31', 'E32' etc.
    next_number: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'doc_type', name='uq_tenant_doctype_seq'),
    )
