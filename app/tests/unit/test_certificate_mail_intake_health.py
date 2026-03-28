from __future__ import annotations

import app.certificate_workflow.mail_intake_service as service


def test_mail_intake_health_disabled(monkeypatch) -> None:
    monkeypatch.setattr(service.settings, "certificate_workflow_mail_intake_enabled", False)
    health = service.check_certificate_mail_intake_health()
    assert health.enabled is False
    assert health.can_connect is False
    assert health.error == "mail_intake_disabled"


def test_mail_intake_health_missing_credentials(monkeypatch) -> None:
    monkeypatch.setattr(service.settings, "certificate_workflow_mail_intake_enabled", True)
    monkeypatch.setattr(service.settings, "certificate_workflow_mail_intake_imap_host", "mail.getupsoft.com.do")
    monkeypatch.setattr(service.settings, "certificate_workflow_mail_intake_imap_user", None)
    monkeypatch.setattr(service.settings, "certificate_workflow_mail_intake_imap_pass", None)
    health = service.check_certificate_mail_intake_health()
    assert health.enabled is True
    assert health.can_connect is False
    assert health.error == "missing_imap_credentials"


def test_mail_intake_health_can_connect(monkeypatch) -> None:
    class _FakeIMAP:
        def __init__(self, host: str, port: int) -> None:
            self.host = host
            self.port = port

        def login(self, _user: str, _password: str) -> None:
            return None

        def select(self, _mailbox: str):
            return "OK", [b""]

        def close(self) -> None:
            return None

        def logout(self) -> None:
            return None

    monkeypatch.setattr(service.settings, "certificate_workflow_mail_intake_enabled", True)
    monkeypatch.setattr(service.settings, "certificate_workflow_mail_intake_imap_host", "mail.getupsoft.com.do")
    monkeypatch.setattr(service.settings, "certificate_workflow_mail_intake_imap_port", 993)
    monkeypatch.setattr(service.settings, "certificate_workflow_mail_intake_imap_user", "certificados@getupsoft.com.do")
    monkeypatch.setattr(service.settings, "certificate_workflow_mail_intake_imap_pass", "secret")
    monkeypatch.setattr(service.settings, "certificate_workflow_mail_intake_use_ssl", True)
    monkeypatch.setattr(service.imaplib, "IMAP4_SSL", _FakeIMAP)

    health = service.check_certificate_mail_intake_health()
    assert health.enabled is True
    assert health.can_connect is True
    assert health.error is None
