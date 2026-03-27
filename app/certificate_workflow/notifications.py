from __future__ import annotations

import httpx
import structlog

from app.infra.settings import settings
from app.services.email_service import EmailConfigurationError, EmailPayload, get_email_service

logger = structlog.get_logger(__name__)


def notify_reminder_due(*, case_id: str, title: str, owner_email: str | None) -> None:
    message = (
        f"Recordatorio vencido para case_id={case_id}\n"
        f"Tarea: {title}\n"
        "Accion requerida: revisar expediente y actualizar estado del workflow."
    )
    _notify_webhook(message)
    _notify_email(owner_email=owner_email, case_id=case_id, title=title, message=message)


def _notify_webhook(message: str) -> None:
    webhook = (settings.notify_slack_webhook or "").strip()
    if not webhook:
        return
    try:
        response = httpx.post(webhook, json={"text": message}, timeout=8.0)
        if response.status_code >= 400:
            logger.warning("certificate_workflow.reminder.webhook_failed", status_code=response.status_code)
    except Exception as exc:  # noqa: BLE001
        logger.warning("certificate_workflow.reminder.webhook_error", error=str(exc))


def _notify_email(*, owner_email: str | None, case_id: str, title: str, message: str) -> None:
    if not owner_email:
        return
    try:
        service = get_email_service()
    except EmailConfigurationError:
        logger.info("certificate_workflow.reminder.email_not_configured", case_id=case_id)
        return
    service.send(
        EmailPayload(
            to=owner_email,
            from_email=settings.notify_email_from or settings.smtp_from,
            subject=f"[DGII] Recordatorio vencido {case_id}",
            text_body=message,
            html_body=f"<p><strong>Case:</strong> {case_id}</p><p><strong>Tarea:</strong> {title}</p>",
        )
    )

