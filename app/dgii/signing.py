from __future__ import annotations

from typing import Optional

from cryptography.hazmat.primitives.serialization import Encoding, pkcs12
from lxml import etree
from signxml import (
    CanonicalizationMethod,
    DigestAlgorithm,
    SignatureConstructionMethod,
    SignatureMethod,
    XMLSigner,
    XMLVerifier,
)

class XMLSigningService:
    def __init__(self, p12_path: str, p12_password: str):
        """
        Initializes the XML signing service with a PKCS#12 certificate.

        :param p12_path: The path to the PKCS#12 file (.p12).
        :param p12_password: The password for the PKCS#12 file.
        """
        with open(p12_path, "rb") as f:
            p12 = pkcs12.load_key_and_certificates(f.read(), p12_password.encode())

        self.private_key = p12[0]
        self.certificate = p12[1]

    def sign_xml(self, xml_content: bytes) -> bytes:
        """
        Signs an XML document using the loaded certificate and private key.

        :param xml_content: The XML content to sign, as bytes.
        :return: The signed XML content, as bytes.
        """
        root = etree.fromstring(xml_content)

        signer = XMLSigner(
            method=SignatureConstructionMethod.enveloped,
            signature_algorithm=SignatureMethod.RSA_SHA256,
            digest_algorithm=DigestAlgorithm.SHA256,
            c14n_algorithm=CanonicalizationMethod.EXCLUSIVE_XML_CANONICALIZATION_1_0,
        )

        signed_root = signer.sign(
            root,
            key=self.private_key,
            cert=self.certificate.public_bytes(Encoding.PEM),
            reference_uri="",
        )

        return etree.tostring(signed_root, encoding="utf-8")


def sign_ecf(xml_content: bytes, p12_path: str, p12_password: Optional[str]) -> bytes:
    """Sign an XML document using a PKCS#12 bundle.

    This is the canonical signing helper used by DGII flows (Semilla, e-CF, RFCE, etc.).
    """

    service = XMLSigningService(p12_path, p12_password or "")
    signed = service.sign_xml(xml_content)
    if not signed:
        raise ValueError("El XML firmado está vacío")
    return signed

def verify_xml_signature(signed_xml_content: bytes, certificate: bytes) -> bool:
    """
    Verifies the digital signature of an XML document.

    :param signed_xml_content: The signed XML content to verify, as bytes.
    :param certificate: The PEM-encoded certificate to use for verification.
    :return: True if the signature is valid, False otherwise.
    """
    try:
        XMLVerifier().verify(signed_xml_content, x509_cert=certificate)
        return True
    except Exception:
        return False
