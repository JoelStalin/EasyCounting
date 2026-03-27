from __future__ import annotations

from app.dgii.domain.xml_signature_service import SignedXmlResult, XmlSignatureService
from app.dgii.domain.xml_signature_verification_service import XmlSignatureVerificationService


class SignEcfUseCase:
    def __init__(self, signer: XmlSignatureService, verifier: XmlSignatureVerificationService):
        self.signer = signer
        self.verifier = verifier

    def execute(self, xml_bytes: bytes, p12_path: str, password: str) -> SignedXmlResult:
        signed = self.signer.sign_xml(xml_bytes, p12_path=p12_path, password=password, reference_uri="")
        verification = self.verifier.verify_signature(signed.xml_signed)
        if not verification.valid:
            raise ValueError("Firma local invalida tras firmado")
        return signed
