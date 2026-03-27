from __future__ import annotations

from app.security.xml_dsig import SignatureValidationResult, validate_signed_xml


class XmlSignatureVerificationService:
    """Verify XMLDSIG integrity and DGII-required algorithms."""

    def verify_signature(self, xml_signed: bytes) -> SignatureValidationResult:
        return validate_signed_xml(xml_signed)
