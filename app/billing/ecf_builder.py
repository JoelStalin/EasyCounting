"""Generador de e-CF."""
from __future__ import annotations

from datetime import datetime, timezone

from jinja2 import Environment, PackageLoader, select_autoescape

from app.billing.validators import validate_encf, validate_rnc

_env = Environment(autoescape=select_autoescape(enabled_extensions=("xml",)))
_template = _env.from_string(
    """<?xml version='1.0' encoding='UTF-8'?>\n<Factura>\n  <Encabezado>\n    <RNCEmisor>{{ rnc_emisor }}</RNCEmisor>\n    <RNCComprador>{{ rnc_comprador }}</RNCComprador>\n    <ENCF>{{ encf }}</ENCF>\n    <FechaEmision>{{ fecha_emision }}</FechaEmision>\n  </Encabezado>\n  <Totales>\n    <Total>{{ total }}</Total>\n  </Totales>\n</Factura>"""
)


def build_ecf(*, encf: str, rnc_emisor: str, rnc_comprador: str, total: float) -> str:
    validate_encf(encf)
    validate_rnc(rnc_emisor)
    validate_rnc(rnc_comprador)
    return _template.render(
        rnc_emisor=rnc_emisor,
        rnc_comprador=rnc_comprador,
        encf=encf,
        total=f"{total:.2f}",
        fecha_emision=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
    )
