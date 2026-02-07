"""Generador de ANECF."""
from __future__ import annotations

from datetime import datetime, timezone

from app.billing.validators import validate_rnc


def build_anecf(*, tipo_ecf: str, rnc_emisor: str, desde: int, hasta: int) -> str:
    if desde <= 0 or hasta <= 0 or desde > hasta:
        raise ValueError("Rango inválido")
    cantidad = hasta - desde + 1
    validate_rnc(rnc_emisor)
    return (
        "<?xml version='1.0' encoding='UTF-8'?>"
        f"<ANECF><TipoECF>{tipo_ecf}</TipoECF><RNCEmisor>{rnc_emisor}</RNCEmisor>"
        f"<Desde>{desde}</Desde><Hasta>{hasta}</Hasta><Cantidad>{cantidad}</Cantidad>"
        f"<Fecha>{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}</Fecha></ANECF>"
    )
