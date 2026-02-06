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

    schema_path = Path(xsd_path).resolve(strict=True)
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
