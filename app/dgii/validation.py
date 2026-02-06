from __future__ import annotations

from pathlib import Path
from lxml import etree

XSD_DIR = Path(__file__).parent.parent.parent / "xsd"


class XSDValidator:
    def __init__(self, xsd_file: str):
        """
        Initializes the XSD validator with a specific XSD schema.

        :param xsd_file: The filename of the XSD schema to use for validation.
        """
        xsd_path = XSD_DIR / xsd_file
        if not xsd_path.exists():
            raise FileNotFoundError(f"XSD schema not found at: {xsd_path}")

        with open(xsd_path, "rb") as f:
            xmlschema_doc = etree.parse(f)
        self.schema = etree.XMLSchema(xmlschema_doc)

    def validate_xml(self, xml_content: bytes) -> bool:
        """
        Validates an XML content against the loaded XSD schema.

        :param xml_content: The XML content to validate, as bytes.
        :return: True if the XML is valid, False otherwise.
        """
        try:
            xml_doc = etree.fromstring(xml_content)
            self.schema.assertValid(xml_doc)
            return True
        except etree.DocumentInvalid:
            return False
        except etree.XMLSyntaxError:
            return False


def validate_xml(xml_content: bytes, xsd_file: str, *, raise_on_error: bool = True) -> bool:
    """Validate an XML document against a known DGII XSD.

    The repository stores official DGII schemas under the top-level `xsd/` folder.
    """

    validator = XSDValidator(xsd_file)
    is_valid = validator.validate_xml(xml_content)
    if is_valid:
        return True
    if raise_on_error:
        raise ValueError(f"XML inválido contra XSD: {xsd_file}")
    return False


def get_validator_for(e_cf_type: str) -> XSDValidator:
    """
    Factory function to get a validator for a specific e-CF type.
    """
    schema_map = {
        "31": "e-CF 31 v.1.0.xsd",
        "32": "e-CF 32 v.1.0.xsd",
        "33": "e-CF 33 v.1.0.xsd",
        "34": "e-CF 34 v.1.0.xsd",
        "41": "e-CF 41 v.1.0.xsd",
        "43": "e-CF 43 v.1.0.xsd",
        "44": "e-CF 44 v.1.0.xsd",
        "45": "e-CF 45 v.1.0.xsd",
        "46": "e-CF 46 v.1.0.xsd",
        "47": "e-CF 47 v.1.0.xsd",
        "ARECF": "ARECF v1.0.xsd",
        "ACECF": "ACECF v.1.0.xsd",
        "ANECF": "ANECF v.1.0.xsd",
        "RFCE": "RFCE 32 v.1.0.xsd",
    }

    xsd_file = schema_map.get(e_cf_type)
    if not xsd_file:
        raise ValueError(f"Unknown e-CF type: {e_cf_type}")

    return XSDValidator(xsd_file)
