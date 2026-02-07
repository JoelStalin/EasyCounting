"""Generador de ARECF."""
from __future__ import annotations

from datetime import datetime, timezone

from app.billing.validators import validate_encf, validate_rnc


def build_arecf(*, encf: str, rnc_emisor: str, rnc_comprador: str, estado: int, motivo_codigo: str | None) -> str:
    validate_encf(encf)
    validate_rnc(rnc_emisor)
    validate_rnc(rnc_comprador)
    if estado == 1 and not motivo_codigo:
        raise ValueError("Debe indicar motivo para estado 1")
    return (
        "<?xml version='1.0' encoding='UTF-8'?>"
        f"<ARECF><ENCF>{encf}</ENCF><RNCEmisor>{rnc_emisor}</RNCEmisor>"
        f"<RNCComprador>{rnc_comprador}</RNCComprador><Estado>{estado}</Estado>"
        f"<CodigoMotivo>{motivo_codigo or ''}</CodigoMotivo><Fecha>{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}</Fecha></ARECF>"
    )
