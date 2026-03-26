"""Base utilities for DGII XML payloads."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Iterable, Tuple

from lxml import etree
from pydantic import BaseModel, ConfigDict


def decimal_to_str(value: Decimal | float | int) -> str:
    """Format decimals using two decimal places."""

    quantized = Decimal(str(value)).quantize(Decimal("0.01"))
    return f"{quantized:.2f}"


@dataclass
class XMLSerializerConfig:
    root_tag: str
    namespace: str | None = None
    nsmap: dict[str, str] | None = None


class BaseDGIIModel(BaseModel):
    """Base class for DGII documents with XML serialization support."""

    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True, arbitrary_types_allowed=True)

    xml_config: ClassVar[XMLSerializerConfig]

    def _create_root(self) -> etree._Element:
        cfg = self.xml_config
        if cfg.namespace:
            return etree.Element(f"{{{cfg.namespace}}}{cfg.root_tag}", nsmap=cfg.nsmap)
        return etree.Element(cfg.root_tag, nsmap=cfg.nsmap)

    def _append(self, parent: etree._Element, tag: str, text: str) -> None:
        element = etree.SubElement(parent, tag)
        element.text = text

    def _build_tree(self) -> etree._Element:
        """Override in subclasses to build document contents."""

        raise NotImplementedError

    def to_xml_bytes(self) -> bytes:
        root = self._build_tree()
        return etree.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=False)

    def _build_key_values(self, parent: etree._Element, rows: Iterable[Tuple[str, str]]) -> None:
        for tag, value in rows:
            self._append(parent, tag, value)
