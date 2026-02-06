"""DGII ENFC reception service handling validation and persistence stubs."""
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
_ECF_XSD_OFFICIAL_BY_TIPO = {
    "31": _BASE_DIR / "xsd" / "e-CF 31 v.1.0.xsd",
    "32": _BASE_DIR / "xsd" / "e-CF 32 v.1.0.xsd",
    "33": _BASE_DIR / "xsd" / "e-CF 33 v.1.0.xsd",
    "34": _BASE_DIR / "xsd" / "e-CF 34 v.1.0.xsd",
    "41": _BASE_DIR / "xsd" / "e-CF 41 v.1.0.xsd",
    "43": _BASE_DIR / "xsd" / "e-CF 43 v.1.0.xsd",
    "44": _BASE_DIR / "xsd" / "e-CF 44 v.1.0.xsd",
    "45": _BASE_DIR / "xsd" / "e-CF 45 v.1.0.xsd",
    "46": _BASE_DIR / "xsd" / "e-CF 46 v.1.0.xsd",
    "47": _BASE_DIR / "xsd" / "e-CF 47 v.1.0.xsd",
}
_ECF_XSD_SIMPLIFIED = _BASE_DIR / "schemas" / "ECF.xsd"


def _extract_tipo_ecf(xml_bytes: bytes) -> str | None:
    try:
        xml_text = xml_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return None
    for tag in ("<TipoeCF>", "<TipoECF>"):
        start = xml_text.find(tag)
        if start == -1:
            continue
        start += len(tag)
        end = xml_text.find("<", start)
        if end == -1:
            continue
        value = xml_text[start:end].strip()
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            return digits
    return None


def _validate_official_ecf(xml_bytes: bytes) -> None:
    tipo = _extract_tipo_ecf(xml_bytes)
    if tipo and tipo in _ECF_XSD_OFFICIAL_BY_TIPO:
        validate_with_xsd(xml_bytes, str(_ECF_XSD_OFFICIAL_BY_TIPO[tipo]))
        return

    last_error: Exception | None = None
    for schema_path in _ECF_XSD_OFFICIAL_BY_TIPO.values():
        try:
            validate_with_xsd(xml_bytes, str(schema_path))
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue

    if last_error:
        raise last_error


def _populate_node(node: Element, value: Any) -> None:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            if isinstance(child_value, list):
                for entry in child_value:
                    child = SubElement(node, child_key)
                    _populate_node(child, entry)
            else:
                child = SubElement(node, child_key)
                _populate_node(child, child_value)
    elif value is not None:
        node.text = str(value)


def _dict_to_xml(payload: Dict[str, Any], root_name: str = "eCF") -> bytes:
    root = Element(root_name)
    _populate_node(root, payload)
    return tostring(root, encoding="utf-8")


def _extract_xml_bytes(payload: Union[str, bytes, Dict[str, Any]]) -> bytes:
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    if isinstance(payload, dict):
        if xml_b64 := payload.get("ecf_xml_b64"):
            return base64.b64decode(xml_b64)
        if xml_dict := payload.get("ecf_json"):
            return _dict_to_xml(xml_dict)
    raise ValueError("Unsupported payload format for e-CF reception")


async def procesar_ecf(payload: Union[str, bytes, Dict[str, Any]]) -> Dict[str, Any]:
    """Validate and persist the incoming e-CF payload, returning an acknowledgement."""

    xml_bytes = _extract_xml_bytes(payload)
    logger.info("recepcion.ecf.decoded", size=len(xml_bytes))

    xml_preview = xml_bytes.lstrip()[:64]
    if xml_preview.startswith(b"<ECF") or xml_preview.startswith(b"<?xml") and b"<ECF" in xml_preview:
        _validate_official_ecf(xml_bytes)
    else:
        validate_with_xsd(xml_bytes, str(_ECF_XSD_SIMPLIFIED))
    if not verify_xml_signature(xml_bytes):
        logger.warning("recepcion.ecf.signature_invalid")
        raise ValueError("Firma inválida del documento e-CF")

    acuse_id = f"ARC-{uuid.uuid4().hex[:12].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info("recepcion.ecf.persisted", acuse_id=acuse_id)

    return {
        "acuseId": acuse_id,
        "estado": "RECIBIDO",
        "detalle": "OK",
        "timestamp": timestamp,
    }
