from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.security.xml_dsig import SigningOptions, sign_xml


@dataclass(slots=True)
class SignedXmlResult:
    xml_signed: bytes
    fingerprint_sha256: str


class XmlSignatureService:
    """Sign XML with DGII XMLDSIG profile."""

    def sign_xml(self, xml_bytes: bytes, p12_path: str, password: str, reference_uri: str = "") -> SignedXmlResult:
        options = SigningOptions(
            signing_mode="pfx",
            pfx_path=p12_path,
            pfx_password=password,
            reference_uri=reference_uri,
            validate_after_sign=True,
        )
        signed = sign_xml(xml_bytes, options)
        fingerprint = hashlib.sha256(signed).hexdigest()
        return SignedXmlResult(xml_signed=signed, fingerprint_sha256=fingerprint)
