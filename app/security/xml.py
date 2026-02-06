"""Secure XML utilities with lightweight schema checks."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from defusedxml.ElementTree import fromstring as secure_fromstring
from lxml import etree
from xml.etree import ElementTree as ET

MAX_XML_BYTES = 2_000_000  # 2 MB
MAX_XML_DEPTH = 64


class XMLSecurityError(ValueError):
    """Raised when XML violates security policies."""


def _depth(node: ET.Element, level: int = 0) -> int:
    children = list(node)
    if not children:
        return level
    return max(_depth(child, level + 1) for child in children)


def parse_secure(xml_bytes: bytes) -> ET.Element:
    """Parse XML bytes with XXE protections and depth/size limits."""

    if len(xml_bytes) > MAX_XML_BYTES:
        raise XMLSecurityError("XML demasiado grande")

    root = secure_fromstring(xml_bytes)
    if _depth(root) > MAX_XML_DEPTH:
        raise XMLSecurityError("XML demasiado profundo")
    return root


def _require_paths(root: ET.Element, paths: Iterable[str]) -> None:
    for path in paths:
        if root.find(path) is None:
            raise XMLSecurityError(f"XML sin elemento requerido: {path}")


def validate_with_xsd(xml_bytes: bytes, xsd_path: str) -> None:
    """Validate XML bytes using a real XSD schema (lxml).

    This function enforces size/depth protections before running XSD validation.
    """

    parse_secure(xml_bytes)

    requested = Path(xsd_path)
    if not requested.is_absolute():
        candidate = (Path.cwd() / requested)
    else:
        candidate = requested

    if not candidate.exists():
        lowered = str(requested).replace("\\", "/").lower()
        if lowered.endswith("xsd/ecf.xsd"):
            xml_text = xml_bytes.decode("utf-8", errors="ignore")
            if "<eCF" in xml_text[:200]:
                candidate = Path.cwd() / "schemas" / "ECF.xsd"
                schema_path = candidate.resolve(strict=True)
                xsd_doc = etree.parse(str(schema_path))
                schema = etree.XMLSchema(xsd_doc)
                parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False, huge_tree=False)
                xml_doc = etree.fromstring(xml_bytes, parser=parser)
                schema.assertValid(xml_doc)
                return
            tipo = None
            for tag in ("<TipoeCF>", "<TipoECF>"):
                start = xml_text.find(tag)
                if start != -1:
                    start += len(tag)
                    end = xml_text.find("<", start)
                    if end != -1:
                        tipo_raw = xml_text[start:end].strip()
                        digits = "".join(ch for ch in tipo_raw if ch.isdigit())
                        if digits:
                            tipo = digits
                            break
            if tipo:
                candidate = Path.cwd() / "xsd" / f"e-CF {tipo} v.1.0.xsd"
            if not candidate.exists():
                candidate = Path.cwd() / "schemas" / "ECF.xsd"
        elif lowered.endswith("xsd/rfce.xsd"):
            candidate = Path.cwd() / "schemas" / "RFCE.xsd"
        elif lowered.endswith("xsd/acecf.xsd"):
            candidate = Path.cwd() / "schemas" / "ACECF.xsd"
        elif lowered.endswith("xsd/arecf.xsd"):
            candidate = Path.cwd() / "schemas" / "ARECF.xsd"
        elif lowered.endswith("xsd/anecf.xsd"):
            candidate = Path.cwd() / "schemas" / "ANECF.xsd"

    schema_path = candidate.resolve(strict=True)
    try:
        xsd_doc = etree.parse(str(schema_path))
        schema = etree.XMLSchema(xsd_doc)
    except OSError as exc:  # pragma: no cover
        raise XMLSecurityError(f"XSD no accesible: {schema_path}") from exc
    except etree.XMLSchemaParseError as exc:  # pragma: no cover
        raise XMLSecurityError(f"XSD inválido: {schema_path}") from exc

    parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False, huge_tree=False)
    try:
        xml_doc = etree.fromstring(xml_bytes, parser=parser)
    except etree.XMLSyntaxError as exc:
        raise XMLSecurityError(f"XML inválido: {exc}") from exc

    try:
        schema.assertValid(xml_doc)
    except etree.DocumentInvalid as exc:
        raise XMLSecurityError(f"XML no cumple XSD: {exc}") from exc


def ensure_elements(elements: Iterable[str], root: ET.Element) -> None:
    """Ensure required elements exist in an XML tree."""

    _require_paths(root, elements)
