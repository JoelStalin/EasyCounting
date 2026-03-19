from __future__ import annotations

import smtplib
from pathlib import Path

import pytest

from app.services.email_service import (
    EmailAttachment,
    EmailConfigurationError,
    EmailDeliveryError,
    EmailPayload,
    SmtpEmailService,
)


class _FakeSmtpClient:
    def __init__(self) -> None:
        self.started_tls = False
        self.logged_in = False
        self.sent = False
        self.message = None
        self.recipients = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def starttls(self, *, context=None):
        self.started_tls = True

    def login(self, user: str, password: str):
        self.logged_in = True

    def send_message(self, message, to_addrs):
        self.sent = True
        self.message = message
        self.recipients = to_addrs


def test_smtp_service_uses_ssl_for_port_465(monkeypatch) -> None:
    fake_client = _FakeSmtpClient()
    monkeypatch.setattr("app.services.email_service.settings.smtp_host", "smtp.example.com")
    monkeypatch.setattr("app.services.email_service.settings.smtp_port", 465)
    monkeypatch.setattr("app.services.email_service.settings.smtp_from", "noreply@example.com")
    monkeypatch.setattr("app.services.email_service.settings.smtp_secure", True)
    monkeypatch.setattr("app.services.email_service.settings.smtp_user", "user")
    monkeypatch.setattr("app.services.email_service.settings.smtp_pass", "pass")
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP_SSL", lambda *args, **kwargs: fake_client)

    service = SmtpEmailService()
    service.send(
        EmailPayload(
            to="client@example.com",
            subject="Hola",
            text_body="Texto",
        )
    )

    assert fake_client.sent is True
    assert fake_client.logged_in is True
    assert fake_client.started_tls is False
    assert fake_client.recipients == ["client@example.com"]


def test_smtp_service_uses_starttls_when_secure_on_non_465(monkeypatch) -> None:
    fake_client = _FakeSmtpClient()
    monkeypatch.setattr("app.services.email_service.settings.smtp_host", "smtp.example.com")
    monkeypatch.setattr("app.services.email_service.settings.smtp_port", 587)
    monkeypatch.setattr("app.services.email_service.settings.smtp_from", "noreply@example.com")
    monkeypatch.setattr("app.services.email_service.settings.smtp_secure", True)
    monkeypatch.setattr("app.services.email_service.settings.smtp_user", "user")
    monkeypatch.setattr("app.services.email_service.settings.smtp_pass", "pass")
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", lambda *args, **kwargs: fake_client)

    service = SmtpEmailService()
    service.send(
        EmailPayload(
            to=["client@example.com", "other@example.com"],
            subject="Hola",
            text_body="Texto",
            html_body="<p>HTML</p>",
        )
    )

    assert fake_client.sent is True
    assert fake_client.logged_in is True
    assert fake_client.started_tls is True
    assert fake_client.recipients == ["client@example.com", "other@example.com"]


def test_smtp_service_supports_attachments(monkeypatch, tmp_path: Path) -> None:
    fake_client = _FakeSmtpClient()
    attachment_path = tmp_path / "demo.txt"
    attachment_path.write_text("demo", encoding="utf-8")
    monkeypatch.setattr("app.services.email_service.settings.smtp_host", "smtp.example.com")
    monkeypatch.setattr("app.services.email_service.settings.smtp_port", 25)
    monkeypatch.setattr("app.services.email_service.settings.smtp_from", "noreply@example.com")
    monkeypatch.setattr("app.services.email_service.settings.smtp_secure", False)
    monkeypatch.setattr("app.services.email_service.settings.smtp_user", None)
    monkeypatch.setattr("app.services.email_service.settings.smtp_pass", None)
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", lambda *args, **kwargs: fake_client)

    service = SmtpEmailService()
    service.send(
        EmailPayload(
            to="client@example.com",
            subject="Adjunto",
            text_body="Texto",
            attachments=[EmailAttachment.from_path(attachment_path)],
        )
    )

    assert fake_client.sent is True
    attachments = list(fake_client.message.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "demo.txt"


def test_smtp_service_requires_minimal_configuration(monkeypatch) -> None:
    monkeypatch.setattr("app.services.email_service.settings.smtp_host", None)
    monkeypatch.setattr("app.services.email_service.settings.smtp_port", None)
    monkeypatch.setattr("app.services.email_service.settings.smtp_from", None)

    with pytest.raises(EmailConfigurationError):
        SmtpEmailService()


def test_smtp_service_wraps_delivery_errors(monkeypatch) -> None:
    class _BrokenClient(_FakeSmtpClient):
        def send_message(self, message, to_addrs):
            raise smtplib.SMTPException("boom")

    broken = _BrokenClient()
    monkeypatch.setattr("app.services.email_service.settings.smtp_host", "smtp.example.com")
    monkeypatch.setattr("app.services.email_service.settings.smtp_port", 25)
    monkeypatch.setattr("app.services.email_service.settings.smtp_from", "noreply@example.com")
    monkeypatch.setattr("app.services.email_service.settings.smtp_secure", False)
    monkeypatch.setattr("app.services.email_service.settings.smtp_user", None)
    monkeypatch.setattr("app.services.email_service.settings.smtp_pass", None)
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", lambda *args, **kwargs: broken)

    service = SmtpEmailService()
    with pytest.raises(EmailDeliveryError):
        service.send(EmailPayload(to="client@example.com", subject="Hola", text_body="Texto"))
