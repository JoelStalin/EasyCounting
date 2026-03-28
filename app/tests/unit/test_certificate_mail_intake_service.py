from __future__ import annotations

from email.message import EmailMessage

from app.certificate_workflow.mail_intake_service import (
    _extract_case_id,
    _extract_password,
    _extract_text_body,
)


def test_extract_case_id_from_text() -> None:
    text = "Solicitud aprobada caso PSC-2026-00017, adjunto certificado."
    assert _extract_case_id(text) == "PSC-2026-00017"


def test_extract_password_from_text() -> None:
    text = "Password: abc123XYZ"
    assert _extract_password(text) == "abc123XYZ"


def test_extract_text_body_plain_message() -> None:
    msg = EmailMessage()
    msg.set_content("Hola\ncase PSC-2026-00017\nclave: secreto123")
    body = _extract_text_body(msg)
    assert "PSC-2026-00017" in body
    assert "secreto123" in body
