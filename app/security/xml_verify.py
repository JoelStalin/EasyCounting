"""XML digital signature verification helpers."""
from __future__ import annotations

from dataclasses import dataclass

from signxml import XMLVerifier

from app.security.xml import parse_secure


@dataclass(frozen=True, slots=True)
class XMLSignatureVerificationResult:
    signed_xml: object
    has_x509_certificate: bool


def verify_xml_signature(xml_bytes: bytes, *, require_x509: bool = False) -> bool:
    """Validate the XML signature using SignXML.

    Args:
        xml_bytes: The XML payload that must contain a Signature element.
        require_x509: If ``True`` the signature must contain an X509 certificate.

    Returns:
        ``True`` when the signature is valid, otherwise ``False``.
    """

    parse_secure(xml_bytes)  # Ensure document passes security guards first.
    try:
        verified = XMLVerifier().verify(xml_bytes)
    except Exception:
        return False
    if require_x509 and not verified.signed_xml.find(".//{*}X509Certificate"):
        return False
    return True


def verify_xml_signature_details(xml_bytes: bytes, *, require_x509: bool = False) -> XMLSignatureVerificationResult:
    """Verify XML signature and return the verified XML tree.

    Raises:
        ValueError: when signature verification fails.
    """

    parse_secure(xml_bytes)
    try:
        verified = XMLVerifier().verify(xml_bytes)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Firma inválida") from exc

    has_x509 = bool(verified.signed_xml.find(".//{*}X509Certificate"))
    if require_x509 and not has_x509:
        raise ValueError("Firma sin certificado X509")

    return XMLSignatureVerificationResult(signed_xml=verified.signed_xml, has_x509_certificate=has_x509)
