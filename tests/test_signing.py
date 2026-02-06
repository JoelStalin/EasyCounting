from __future__ import annotations

from cryptography.hazmat.primitives.serialization import Encoding
from signxml import SignatureMethod

from app.dgii.signing import XMLSigningService, verify_xml_signature


def test_xml_signing_service(certificate_bundle):
    """Tests that the XMLSigningService can sign an XML document."""

    p12_path, password, _key, cert_obj = certificate_bundle
    service = XMLSigningService(str(p12_path), password.decode())
    xml_content = b"<root><data>Hello, World!</data></root>"
    signed_xml = service.sign_xml(xml_content)

    cert = cert_obj.public_bytes(Encoding.PEM)
    assert b"Signature" in signed_xml
    assert SignatureMethod.RSA_SHA256.value.encode() in signed_xml
    assert verify_xml_signature(signed_xml, cert) is True


def test_verify_xml_signature_invalid(certificate_bundle):
    """Tests that verify_xml_signature returns False for an invalid signature."""

    p12_path, password, _key, cert_obj = certificate_bundle
    _ = (p12_path, password)
    xml_content = b"<root><data>Hello, World!</data></root>"
    cert = cert_obj.public_bytes(Encoding.PEM)

    assert verify_xml_signature(xml_content, cert) is False
