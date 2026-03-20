"""
ECF Engine — Motor Maestro de Comprobantes Electrónicos.
Self-contained async router using native app async session patterns.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint, func, select, update, insert, text

from app.db import get_async_session, sync_engine
from app.models.base import Base

router = APIRouter()

# ──────────────────────────────────────────────────────────────────
# Self-contained table definition (avoids ORM circular imports)
# ──────────────────────────────────────────────────────────────────
_sequences_t = Table(
    "sequences", Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tenant_id", Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
    Column("doc_type", String(10), nullable=False),
    Column("prefix", String(3), nullable=False),
    Column("next_number", Integer, default=1),
    UniqueConstraint("tenant_id", "doc_type", name="uq_tenant_doctype_seq"),
    extend_existing=True,
)

# Create sequences table synchronously at module load (safe, uses checkfirst)
with sync_engine.begin() as _conn:
    Base.metadata.create_all(bind=_conn, checkfirst=True)


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────
def _next_seq_sync(tenant_id: int, doc_type: str) -> str:
    """Fetch-and-increment the sequence counter synchronously."""
    prefix = f"E{doc_type}"
    with sync_engine.begin() as conn:
        row = conn.execute(
            select(_sequences_t).where(
                (_sequences_t.c.tenant_id == tenant_id) &
                (_sequences_t.c.doc_type == doc_type)
            )
        ).fetchone()
        if row is None:
            conn.execute(
                insert(_sequences_t).values(
                    tenant_id=tenant_id, doc_type=doc_type, prefix=prefix, next_number=2
                )
            )
            return f"{prefix}{str(1).zfill(8)}"
        ncf = f"{row.prefix}{str(row.next_number).zfill(8)}"
        conn.execute(
            update(_sequences_t)
            .where(
                (_sequences_t.c.tenant_id == tenant_id) &
                (_sequences_t.c.doc_type == doc_type)
            )
            .values(next_number=row.next_number + 1)
        )
    return ncf


# ──────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────
@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_ecf(payload: Dict[str, Any]):
    """
    Motor Maestro: valida cuota, asigna NCF, registra uso.
    Retorna JSON para que Odoo contabilice el comprobante.
    """
    from app.models.tenant import Tenant
    from app.models.billing import Plan, UsageRecord

    tenant_id = payload.get("certia_tenant_id")
    doc_type = str(payload.get("l10n_latam_document_type", "31"))

    async with get_async_session() as db:
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant no encontrado.")

        plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
        if not plan:
            raise HTTPException(status_code=403, detail="Sin Plan de Suscripción.")

        # Cuota mensual
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        from sqlalchemy import select as sa_select
        result = await db.execute(
            sa_select(func.count(UsageRecord.id)).where(
                UsageRecord.tenant_id == tenant_id,
                UsageRecord.fecha >= month_start,
            )
        )
        usage_count = result.scalar() or 0

        if plan.max_facturas_mes > 0 and usage_count >= plan.max_facturas_mes:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Límite excedido. Plan '{plan.name}': {plan.max_facturas_mes} e-CF/mes.",
            )

        ncf = _next_seq_sync(tenant_id, doc_type)

        usage = UsageRecord(
            tenant_id=tenant_id,
            plan_id=plan.id,
            ecf_type=doc_type,
            track_id=f"TRK-{ncf}",
        )
        db.add(usage)
        await db.flush()
        track_id = usage.track_id

    return {
        "status": "GENERATED",
        "ncf": ncf,
        "track_id": track_id,
        "message": f"e-CF {doc_type} generado por Certia API.",
        "quota": {"used": usage_count + 1, "max": plan.max_facturas_mes},
        "odoo_payload": {
            "partner_vat": payload.get("partner_vat"),
            "amount_total": payload.get("amount_total", 0.0),
            "date": datetime.utcnow().isoformat(),
        },
    }


@router.get("/sync")
async def sync_ecf_for_odoo(tenant_id: int = Query(...)):
    """Endpoint que Odoo usa para traer todos los e-CFs recientes del tenant."""
    from app.models.tenant import Tenant
    from app.models.billing import UsageRecord
    from sqlalchemy import select as sa_select

    async with get_async_session() as db:
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant no encontrado.")

        result = await db.execute(
            sa_select(UsageRecord)
            .where(UsageRecord.tenant_id == tenant_id)
            .order_by(UsageRecord.fecha.desc())
            .limit(100)
        )
        records = result.scalars().all()

    data = [
        {
            "ncf": f"E{r.ecf_type}{str(r.id).zfill(8)}",
            "doc_type": r.ecf_type,
            "track_id": r.track_id,
            "amount_total": 0.0,
            "date": r.fecha.isoformat() if r.fecha else None,
            "description": f"e-CF {r.ecf_type} — Certia API",
        }
        for r in records
    ]
    return {"status": "ok", "tenant": tenant.name, "count": len(data), "data": data}
