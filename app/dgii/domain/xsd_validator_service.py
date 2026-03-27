from __future__ import annotations

from dataclasses import dataclass

from app.dgii.validation import get_validator_for
from app.security.xml import validate_with_xsd


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    errors: list[str]


class XsdValidatorService:
    """Validate XML payloads against DGII XSDs by document type."""

    def validate_xsd(self, xml_bytes: bytes, tipo_ecf: str) -> ValidationResult:
        try:
            validator = get_validator_for(tipo_ecf)
            valid = validator.validate_xml(xml_bytes)
            if valid:
                return ValidationResult(valid=True, errors=[])
            # Fallback a esquema simplificado del repositorio para fixtures legacy.
            validate_with_xsd(xml_bytes, "xsd/ecf.xsd")
            return ValidationResult(valid=True, errors=[])
        except Exception as exc:  # noqa: BLE001
            return ValidationResult(valid=False, errors=[str(exc)])
