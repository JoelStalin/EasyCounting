"""Service responsible for DGII ENFC commercial approval submissions."""
from __future__ import annotations

import base64
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Union
from xml.etree.ElementTree import Element, SubElement, tostring

import structlog

from app.security.xml import validate_with_xsd
from app.security.xml_verify import verify_xml_signature

logger = structlog.get_logger(__name__)

_BASE_DIR = Path(__file__).resolve().parents[2]
_APROBACION_XSD_OFFICIAL = _BASE_DIR / "xsd" / "ACECF v.1.0.xsd"
_APROBACION_XSD_SIMPLIFIED = _BASE_DIR / "schemas" / "ACECF.xsd"


def _populate_node(node: Element, value: Any) -> None:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            child = SubElement(node, child_key)
            _populate_node(child, child_value)
    elif isinstance(value, list):
        for item in value:
            child = SubElement(node, node.tag)
            _populate_node(child, item)
    elif value is not None:
        node.text = str(value)


def _dict_to_xml(payload: Dict[str, Any], root_name: str = "ACECF") -> bytes:
    root = Element(root_name)
    _populate_node(root, payload)
    return tostring(root, encoding="utf-8")


def _extract_xml(payload: Union[str, bytes, Dict[str, Any]]) -> bytes:
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    if isinstance(payload, dict):
        if xml_b64 := payload.get("aprobacion_xml_b64"):
            return base64.b64decode(xml_b64)
        if xml_dict := payload.get("aprobacion_json"):
            return _dict_to_xml(xml_dict)
    raise ValueError("Unsupported payload format for aprobación comercial")


async def procesar_aprobacion(payload: Union[str, bytes, Dict[str, Any]]) -> Dict[str, Any]:
    """Validate approval payloads and return an acknowledgement."""

    xml_bytes = _extract_xml(payload)
    logger.info("aprobacion.ecf.decoded", size=len(xml_bytes))

    xml_preview = xml_bytes.lstrip()[:256]
    if b"DetalleAprobacionComercial" in xml_preview:
        validate_with_xsd(xml_bytes, str(_APROBACION_XSD_OFFICIAL))
    else:
        validate_with_xsd(xml_bytes, str(_APROBACION_XSD_SIMPLIFIED))

    if not verify_xml_signature(xml_bytes):
        logger.warning("aprobacion.ecf.signature_invalid")
        raise ValueError("Firma inválida del documento de aprobación comercial")

    acuse_id = f"AC-{uuid.uuid4().hex[:10].upper()}"
    estado = "ACEPTADO"
    detalle = "OK"
    logger.info("aprobacion.ecf.persisted", acuse_id=acuse_id)

    return {"acuseId": acuse_id, "estado": estado, "detalle": detalle, "timestamp": datetime.now(timezone.utc).isoformat()}
