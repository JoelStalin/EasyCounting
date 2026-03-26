"""XML Digital Signature helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.serialization import Encoding, pkcs12
from lxml import etree
from signxml import XMLSigner, methods

from app.security.xml import parse_secure


class SigningError(RuntimeError):
    """Raised when digital signing fails."""


def sign_xml_enveloped(xml_bytes: bytes, p12_path: str, password: Optional[str], reference_uri: str = "") -> bytes:
    """Sign XML using RSA-SHA256 enveloped signature."""

    root = parse_secure(xml_bytes)

    try:
        bundle = Path(p12_path).read_bytes()
    except OSError as exc:
        raise SigningError("Unable to read PKCS#12 bundle") from exc

    try:
        private_key, certificate, _ = pkcs12.load_key_and_certificates(bundle, password.encode() if password else None)
    except Exception as exc:  # noqa: BLE001
        raise SigningError("Invalid PKCS#12 bundle or password") from exc

    if not private_key or not certificate:
        raise SigningError("PKCS#12 bundle missing private key or certificate")

    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm="rsa-sha256",
        digest_algorithm="sha256",
        c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
    )

    try:
        signed = signer.sign(
            root,
            key=private_key,
            cert=certificate.public_bytes(Encoding.PEM),
            reference_uri=reference_uri or None,
        )
    except Exception as exc:  # noqa: BLE001
        raise SigningError("Error signing XML document") from exc

    return etree.tostring(signed, encoding="UTF-8", xml_declaration=True)
