"""Rutas de emisión y administración de comprobantes."""
from __future__ import annotations

import base64

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.billing.acecf_builder import build_acecf
from app.billing.anecf_builder import build_anecf
from app.billing.arecf_builder import build_arecf
from app.billing.ecf_builder import build_ecf
from app.billing.rfce_builder import build_rfce
from app.shared.utils import ensure_utf8
from app.shared.database import get_db
from app.models.tenant import Tenant

router = APIRouter()


def _get_tenant_or_404(db: Session, tenant_id: int) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return tenant


@router.post("/{tenant}/billing/ecf")
async def create_ecf(tenant: int, payload: dict, db: Session = Depends(get_db)) -> dict:
    tenant_obj = _get_tenant_or_404(db, tenant)
    xml = build_ecf(
        encf=payload["encf"],
        rnc_emisor=tenant_obj.rnc,
        rnc_comprador=payload["rnc_comprador"],
        total=float(payload["total"]),
    )
    return {"xml": xml}


@router.post("/{tenant}/billing/rfce")
async def create_rfce(tenant: int, payload: dict, db: Session = Depends(get_db)) -> dict:
    tenant_obj = _get_tenant_or_404(db, tenant)
    xml = build_rfce(encf=payload["encf"], rnc_emisor=tenant_obj.rnc, total=float(payload["total"]))
    return {"xml": xml}


@router.post("/{tenant}/billing/arecf")
async def create_arecf(tenant: int, payload: dict, db: Session = Depends(get_db)) -> dict:
    tenant_obj = _get_tenant_or_404(db, tenant)
    xml = build_arecf(
        encf=payload["encf"],
        rnc_emisor=tenant_obj.rnc,
        rnc_comprador=payload["rnc_comprador"],
        estado=int(payload["estado"]),
        motivo_codigo=payload.get("motivo_codigo"),
    )
    return {"xml": xml}


@router.post("/{tenant}/billing/acecf")
async def create_acecf(tenant: int, payload: dict, db: Session = Depends(get_db)) -> dict:
    tenant_obj = _get_tenant_or_404(db, tenant)
    xml = build_acecf(
        encf=payload["encf"],
        rnc_emisor=tenant_obj.rnc,
        rnc_comprador=payload["rnc_comprador"],
        estado=int(payload["estado"]),
        detalle_motivo=payload.get("detalle_motivo"),
    )
    return {"xml": xml}


@router.post("/{tenant}/billing/anecf")
async def create_anecf(tenant: int, payload: dict, db: Session = Depends(get_db)) -> dict:
    tenant_obj = _get_tenant_or_404(db, tenant)
    xml = build_anecf(
        tipo_ecf=payload["tipo_ecf"],
        rnc_emisor=tenant_obj.rnc,
        desde=int(payload["desde"]),
        hasta=int(payload["hasta"]),
    )
    return {"xml": xml}
