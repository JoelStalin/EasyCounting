"""Reusable SMTP email service."""
from __future__ import annotations

from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path
import mimetypes
import smtplib
import ssl
from typing import Protocol, Sequence

import structlog

from app.infra.settings import settings

logger = structlog.get_logger(__name__)


class EmailConfigurationError(RuntimeError):
    """Raised when SMTP settings are incomplete or invalid."""


class EmailDeliveryError(RuntimeError):
    """Raised when a message cannot be delivered through SMTP."""


@dataclass(slots=True)
class EmailAttachment:
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"

    @classmethod
    def from_path(cls, path: str | Path, *, content_type: str | None = None) -> "EmailAttachment":
        file_path = Path(path)
        guessed_type, _encoding = mimetypes.guess_type(file_path.name)
        resolved_type = content_type or guessed_type or "application/octet-stream"
        return cls(filename=file_path.name, content=file_path.read_bytes(), content_type=resolved_type)


@dataclass(slots=True)
class EmailPayload:
    to: str | Sequence[str]
    subject: str
    text_body: str
    html_body: str | None = None
    attachments: list[EmailAttachment] = field(default_factory=list)
    from_email: str | None = None


class EmailSender(Protocol):
    def send(self, payload: EmailPayload) -> None:
        """Send the email payload."""


def _ensure_smtp_settings() -> None:
    if not settings.smtp_host or not settings.smtp_port or not settings.smtp_from:
        raise EmailConfigurationError("SMTP no configurado; define SMTP_HOST, SMTP_PORT y SMTP_FROM")


def _normalize_recipients(recipients: str | Sequence[str]) -> list[str]:
    if isinstance(recipients, str):
        result = [recipients.strip()]
    else:
        result = [str(item).strip() for item in recipients]
    return [recipient for recipient in result if recipient]


class SmtpEmailService:
    """SMTP implementation with implicit SSL or STARTTLS depending on config."""

    def __init__(self) -> None:
        _ensure_smtp_settings()

    def _build_message(self, payload: EmailPayload) -> tuple[EmailMessage, list[str]]:
        recipients = _normalize_recipients(payload.to)
        if not recipients:
            raise EmailConfigurationError("Debe indicar al menos un destinatario")

        message = EmailMessage()
        message["From"] = payload.from_email or settings.smtp_from or ""
        message["To"] = ", ".join(recipients)
        message["Subject"] = payload.subject
        message.set_content(payload.text_body)
        if payload.html_body:
            message.add_alternative(payload.html_body, subtype="html")

        for attachment in payload.attachments:
            maintype, subtype = attachment.content_type.split("/", 1)
            message.add_attachment(
                attachment.content,
                maintype=maintype,
                subtype=subtype,
                filename=attachment.filename,
            )
        return message, recipients

    def send(self, payload: EmailPayload) -> None:
        message, recipients = self._build_message(payload)
        secure = bool(settings.smtp_secure)
        port = int(settings.smtp_port or 0)
        logger.info(
            "email.send.start",
            smtp_host=settings.smtp_host,
            smtp_port=port,
            smtp_secure=secure,
            recipient_count=len(recipients),
            attachment_count=len(payload.attachments),
        )
        context = ssl.create_default_context()
        try:
            if secure and port == 465:
                with smtplib.SMTP_SSL(
                    settings.smtp_host,
                    port,
                    timeout=settings.smtp_timeout_seconds,
                    context=context,
                ) as client:
                    self._authenticate_and_send(client, recipients, message)
            else:
                with smtplib.SMTP(
                    settings.smtp_host,
                    port,
                    timeout=settings.smtp_timeout_seconds,
                ) as client:
                    if secure:
                        client.starttls(context=context)
                    self._authenticate_and_send(client, recipients, message)
        except (smtplib.SMTPException, OSError) as exc:
            logger.error(
                "email.send.error",
                smtp_host=settings.smtp_host,
                smtp_port=port,
                smtp_secure=secure,
                error=str(exc),
            )
            raise EmailDeliveryError("No se pudo enviar el correo mediante SMTP") from exc

        logger.info(
            "email.send.success",
            smtp_host=settings.smtp_host,
            smtp_port=port,
            smtp_secure=secure,
            recipient_count=len(recipients),
        )

    @staticmethod
    def _authenticate_and_send(client: smtplib.SMTP, recipients: list[str], message: EmailMessage) -> None:
        if settings.smtp_user and settings.smtp_pass:
            client.login(settings.smtp_user, settings.smtp_pass)
        client.send_message(message, to_addrs=recipients)


def get_email_service() -> EmailSender:
    return SmtpEmailService()
