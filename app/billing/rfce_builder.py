"""Generador de RFCE."""
from __future__ import annotations

from datetime import datetime, timezone

from app.billing.validators import validate_encf, validate_rnc


def build_rfce(*, encf: str, rnc_emisor: str, total: float) -> str:
    validate_encf(encf)
    validate_rnc(rnc_emisor)
    return (
        "<?xml version='1.0' encoding='UTF-8'?>"
        f"<Resumen><RNCEmisor>{rnc_emisor}</RNCEmisor><ENCF>{encf}</ENCF>"
        f"<Total>{total:.2f}</Total><Fecha>{datetime.now(timezone.utc).replace(tzinfo=None).date().isoformat()}</Fecha></Resumen>"
    )
