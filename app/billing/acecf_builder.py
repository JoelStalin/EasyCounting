"""Generador de ACECF."""
from __future__ import annotations

from datetime import datetime, timezone

from app.billing.validators import validate_encf, validate_rnc


def build_acecf(*, encf: str, rnc_emisor: str, rnc_comprador: str, estado: int, detalle_motivo: str | None) -> str:
    validate_encf(encf)
    validate_rnc(rnc_emisor)
    validate_rnc(rnc_comprador)
    if estado == 2 and not detalle_motivo:
        raise ValueError("Debe indicar detalle de motivo para rechazos")
    return (
        "<?xml version='1.0' encoding='UTF-8'?>"
        f"<ACECF><ENCF>{encf}</ENCF><RNCEmisor>{rnc_emisor}</RNCEmisor>"
        f"<RNCComprador>{rnc_comprador}</RNCComprador><Estado>{estado}</Estado>"
        f"<DetalleMotivo>{detalle_motivo or ''}</DetalleMotivo><Fecha>{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}</Fecha></ACECF>"
    )
