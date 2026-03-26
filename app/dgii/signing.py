"""DGII signing compatibility helpers."""
from __future__ import annotations

from typing import Optional

from app.security.signing import SigningOptions, sign_xml, validate_signed_xml_details


class XMLSigningService:
    """Compatibility wrapper used by legacy code/tests."""

    def __init__(self, p12_path: str, p12_password: str):
        self._p12_path = p12_path
        self._p12_password = p12_password

    def sign_xml(self, xml_content: bytes) -> bytes:
        options = SigningOptions(
            signing_mode="pfx",
            pfx_path=self._p12_path,
            pfx_password=self._p12_password,
            validate_after_sign=True,
            reference_uri="",
        )
        return sign_xml(xml_content, options)


def sign_ecf(xml_content: bytes, p12_path: str, p12_password: Optional[str]) -> bytes:
    """Sign XML with DGII profile (enveloped, C14N, RSA-SHA256, Digest SHA-256)."""

    service = XMLSigningService(p12_path, p12_password or "")
    signed = service.sign_xml(xml_content)
    if not signed:
        raise ValueError("El XML firmado esta vacio")
    return signed


def verify_xml_signature(signed_xml_content: bytes, certificate: bytes) -> bool:  # noqa: ARG001
    """Validate signature integrity and DGII-required algorithms.

    The ``certificate`` argument is kept for backward compatibility.
    """

    result = validate_signed_xml_details(signed_xml_content, x509_cert=certificate)
    return result.valid
