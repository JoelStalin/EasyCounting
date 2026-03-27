from __future__ import annotations

from pathlib import Path

import pytest

from app.dgii.domain.qr_payload_service import QrPayloadService
from app.dgii.domain.security_code_service import SecurityCodeService


EXPECTED_IDS = [f"F{i:03d}" for i in range(1, 31)]


def test_f001_f030_matrix_contains_all_required_ids() -> None:
    content = Path("docs/certificacion-dgii/matriz-casos.md").read_text(encoding="utf-8")
    missing = [case_id for case_id in EXPECTED_IDS if case_id not in content]
    assert not missing, f"Casos faltantes en matriz funcional: {missing}"


@pytest.mark.parametrize("encf,rnc,fingerprint", [
    ("E310000000001", "131234567", "a" * 64),
    ("E320000000002", "101010101", "b" * 64),
])
def test_security_code_is_reproducible(encf: str, rnc: str, fingerprint: str) -> None:
    service = SecurityCodeService()
    payload = {"encf": encf, "rnc_emisor": rnc}
    first = service.derive_security_code(payload, fingerprint)
    second = service.derive_security_code(payload, fingerprint)
    assert first == second
    assert len(first) == 6


def test_qr_payload_contains_required_fields() -> None:
    qr_service = QrPayloadService()
    invoice_data = {"encf": "E310000000001", "rnc_emisor": "131234567", "monto_total": "100.00"}
    track_status = {"track_id": "TRK123", "estado": "ACEPTADO"}
    payload = qr_service.build_qr_payload(invoice_data, track_status)
    assert "encf=E310000000001" in payload
    assert "rnc=131234567" in payload
    assert "trackId=TRK123" in payload
    assert "estado=ACEPTADO" in payload
