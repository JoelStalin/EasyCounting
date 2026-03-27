from __future__ import annotations

from typing import Any

from lxml import etree


class XmlBuilderService:
    """Build deterministic XML payloads for DGII workflows."""

    def build_xml(self, tipo_ecf: str, payload: dict[str, Any]) -> bytes:
        root = etree.Element("ECF")
        etree.SubElement(root, "TipoeCF").text = str(tipo_ecf)
        for key in sorted(payload.keys()):
            value = payload[key]
            if value is None:
                continue
            node = etree.SubElement(root, key)
            node.text = str(value)
        return etree.tostring(root, encoding="UTF-8", xml_declaration=True)
