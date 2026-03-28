from __future__ import annotations

import email
import imaplib
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import Message
from email.utils import parseaddr
from pathlib import Path

from app.certificate_workflow.certificate_validation import validate_p12_file
from app.certificate_workflow.models import WorkflowStatus
from app.certificate_workflow.persistence import CertificateWorkflowRepository
from app.certificate_workflow.secrets import SecretStoreError, store_certificate_secret
from app.infra.settings import settings
from app.shared.database import session_scope

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MailIntakeStats:
    scanned: int = 0
    skipped_sender: int = 0
    skipped_case: int = 0
    attachments_saved: int = 0
    cases_updated: int = 0
    validations_ok: int = 0
    validations_failed: int = 0


@dataclass(slots=True)
class MailIntakeHealth:
    enabled: bool
    imap_host: str | None
    imap_port: int
    mailbox: str
    use_ssl: bool
    can_connect: bool
    error: str | None = None


def _extract_text_body(message: Message) -> str:
    parts: list[str] = []
    if message.is_multipart():
        for part in message.walk():
            ctype = (part.get_content_type() or "").lower()
            if ctype != "text/plain":
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                parts.append(payload.decode(charset, errors="ignore"))
            except Exception:
                parts.append(payload.decode("utf-8", errors="ignore"))
    else:
        payload = message.get_payload(decode=True)
        if payload:
            charset = message.get_content_charset() or "utf-8"
            parts.append(payload.decode(charset, errors="ignore"))
    return "\n".join(parts).strip()


def _extract_case_id(text: str) -> str | None:
    regex = settings.certificate_workflow_mail_intake_subject_case_regex
    match = re.search(regex, text or "")
    if not match:
        return None
    return match.group(1).strip().upper()


def _extract_password(text: str) -> str | None:
    regex = settings.certificate_workflow_mail_intake_password_regex
    match = re.search(regex, text or "")
    if not match:
        return None
    return (match.group(1) or "").strip()


def _sender_allowed(message: Message) -> bool:
    sender = parseaddr(message.get("From", ""))[1].lower()
    if "@" not in sender:
        return False
    domain = sender.split("@", 1)[1].strip()
    allowed = settings.certificate_workflow_mail_intake_allowed_sender_domains
    return domain in allowed


def _iter_cert_attachments(message: Message) -> list[tuple[str, bytes]]:
    max_bytes = settings.certificate_workflow_mail_intake_attachment_max_mb * 1024 * 1024
    found: list[tuple[str, bytes]] = []
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        filename = (part.get_filename() or "").strip()
        if not filename:
            continue
        lower = filename.lower()
        if not (lower.endswith(".p12") or lower.endswith(".pfx")):
            continue
        payload = part.get_payload(decode=True) or b""
        if not payload or len(payload) > max_bytes:
            continue
        found.append((filename, payload))
    return found


def _write_attachment(case_id: str, filename: str, payload: bytes) -> Path:
    base = settings.storage_base_path / "certificate_mail_intake" / case_id
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    clean_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    path = base / f"{stamp}_{clean_name}"
    path.write_bytes(payload)
    return path


def process_certificate_mail_intake(limit: int = 25) -> MailIntakeStats:
    stats = MailIntakeStats()
    if not settings.certificate_workflow_mail_intake_enabled:
        return stats
    if not settings.certificate_workflow_mail_intake_imap_host:
        logger.warning("certificate_workflow.mail_intake.disabled_missing_imap_host")
        return stats
    if not settings.certificate_workflow_mail_intake_imap_user or not settings.certificate_workflow_mail_intake_imap_pass:
        logger.warning("certificate_workflow.mail_intake.disabled_missing_imap_credentials")
        return stats

    imap: imaplib.IMAP4 | imaplib.IMAP4_SSL
    if settings.certificate_workflow_mail_intake_use_ssl:
        imap = imaplib.IMAP4_SSL(
            settings.certificate_workflow_mail_intake_imap_host,
            settings.certificate_workflow_mail_intake_imap_port,
        )
    else:
        imap = imaplib.IMAP4(
            settings.certificate_workflow_mail_intake_imap_host,
            settings.certificate_workflow_mail_intake_imap_port,
        )

    try:
        imap.login(
            settings.certificate_workflow_mail_intake_imap_user,
            settings.certificate_workflow_mail_intake_imap_pass,
        )
        imap.select(settings.certificate_workflow_mail_intake_imap_mailbox)
        status, data = imap.search(None, "UNSEEN")
        if status != "OK" or not data:
            return stats
        msg_ids = list(reversed((data[0] or b"").split()))
        if limit > 0:
            msg_ids = msg_ids[:limit]

        for msg_id in msg_ids:
            stats.scanned += 1
            fetch_status, raw_data = imap.fetch(msg_id, "(RFC822)")
            if fetch_status != "OK" or not raw_data:
                continue
            raw_msg = raw_data[0][1] if isinstance(raw_data[0], tuple) else None
            if not raw_msg:
                continue
            message = email.message_from_bytes(raw_msg)
            if not _sender_allowed(message):
                stats.skipped_sender += 1
                imap.store(msg_id, "+FLAGS", "\\Seen")
                continue

            subject = message.get("Subject", "") or ""
            body_text = _extract_text_body(message)
            case_id = _extract_case_id(f"{subject}\n{body_text}")
            if not case_id:
                stats.skipped_case += 1
                imap.store(msg_id, "+FLAGS", "\\Seen")
                continue

            attachments = _iter_cert_attachments(message)
            password = _extract_password(body_text)

            with session_scope() as db:
                repo = CertificateWorkflowRepository(db)
                try:
                    request_row = repo.get_request(case_id)
                except Exception:
                    stats.skipped_case += 1
                    imap.store(msg_id, "+FLAGS", "\\Seen")
                    continue

                repo.append_event(
                    request_row=request_row,
                    event_type="MAIL_INTAKE_EMAIL_RECEIVED",
                    payload={
                        "subject": subject[:300],
                        "from": parseaddr(message.get("From", ""))[1],
                        "attachments": [name for name, _ in attachments],
                        "password_detected": bool(password),
                    },
                )

                for filename, payload in attachments:
                    saved_path = _write_attachment(case_id, filename, payload)
                    stats.attachments_saved += 1
                    request_row.status = WorkflowStatus.CERTIFICATE_RECEIVED.value
                    repo.append_event(
                        request_row=request_row,
                        event_type=WorkflowStatus.CERTIFICATE_RECEIVED.value,
                        payload={"file_name": filename, "artifact_path": str(saved_path)},
                    )

                    if not settings.certificate_workflow_mail_intake_auto_validate:
                        continue
                    if not password:
                        repo.append_event(
                            request_row=request_row,
                            event_type="MAIL_INTAKE_PASSWORD_MISSING",
                            payload={"file_name": filename},
                        )
                        continue

                    validation = validate_p12_file(
                        file_path=saved_path,
                        password=password,
                        expected_subject=settings.dgii_cert_expected_subject,
                        expected_serial=settings.dgii_cert_expected_serial,
                        expected_rnc=settings.dgii_cert_expected_rnc or request_row.rnc,
                    )
                    parsed_not_before = (
                        datetime.fromisoformat(validation.not_before) if validation.not_before else None
                    )
                    parsed_not_after = datetime.fromisoformat(validation.not_after) if validation.not_after else None
                    repo.create_validation(
                        case_id=case_id,
                        file_name=filename,
                        sha256=validation.sha256 or "",
                        subject=validation.subject,
                        serial_number=validation.serial_number,
                        not_before=parsed_not_before,
                        not_after=parsed_not_after,
                        has_private_key=validation.has_private_key,
                        password_ok=validation.password_ok,
                        valid=validation.valid,
                        error=validation.error,
                    )

                    if validation.valid:
                        request_row.status = WorkflowStatus.CERTIFICATE_VALIDATED.value
                        repo.append_event(
                            request_row=request_row,
                            event_type=WorkflowStatus.CERTIFICATE_VALIDATED.value,
                            payload={
                                "sha256": validation.sha256,
                                "subject": validation.subject,
                                "serial_number": validation.serial_number,
                            },
                        )
                        try:
                            secret_ref = store_certificate_secret(
                                case_id=case_id,
                                certificate_bytes=payload,
                                certificate_password=password,
                                metadata={
                                    "subject": validation.subject,
                                    "serial_number": validation.serial_number,
                                    "fingerprint_sha1": validation.fingerprint_sha1,
                                    "not_after": validation.not_after,
                                    "source": "mail_intake",
                                },
                            )
                            repo.set_secret_ref(case_id=case_id, secret_ref=secret_ref)
                        except SecretStoreError as exc:
                            repo.append_event(
                                request_row=request_row,
                                event_type="MAIL_INTAKE_SECRET_STORE_FAILED",
                                payload={"error": str(exc)},
                            )
                        stats.validations_ok += 1
                    else:
                        request_row.status = WorkflowStatus.CERTIFICATE_VALIDATION_FAILED.value
                        repo.append_event(
                            request_row=request_row,
                            event_type=WorkflowStatus.CERTIFICATE_VALIDATION_FAILED.value,
                            payload={"error": validation.error, "sha256": validation.sha256},
                        )
                        stats.validations_failed += 1

                if attachments:
                    stats.cases_updated += 1
            imap.store(msg_id, "+FLAGS", "\\Seen")
    finally:
        try:
            imap.close()
        except Exception:
            pass
        try:
            imap.logout()
        except Exception:
            pass

    return stats


def check_certificate_mail_intake_health() -> MailIntakeHealth:
    enabled = settings.certificate_workflow_mail_intake_enabled
    host = settings.certificate_workflow_mail_intake_imap_host
    port = settings.certificate_workflow_mail_intake_imap_port
    mailbox = settings.certificate_workflow_mail_intake_imap_mailbox
    use_ssl = settings.certificate_workflow_mail_intake_use_ssl

    if not enabled:
        return MailIntakeHealth(
            enabled=False,
            imap_host=host,
            imap_port=port,
            mailbox=mailbox,
            use_ssl=use_ssl,
            can_connect=False,
            error="mail_intake_disabled",
        )
    if not host:
        return MailIntakeHealth(
            enabled=True,
            imap_host=None,
            imap_port=port,
            mailbox=mailbox,
            use_ssl=use_ssl,
            can_connect=False,
            error="missing_imap_host",
        )
    if not settings.certificate_workflow_mail_intake_imap_user or not settings.certificate_workflow_mail_intake_imap_pass:
        return MailIntakeHealth(
            enabled=True,
            imap_host=host,
            imap_port=port,
            mailbox=mailbox,
            use_ssl=use_ssl,
            can_connect=False,
            error="missing_imap_credentials",
        )

    imap: imaplib.IMAP4 | imaplib.IMAP4_SSL
    try:
        if use_ssl:
            imap = imaplib.IMAP4_SSL(host, port)
        else:
            imap = imaplib.IMAP4(host, port)
        imap.login(
            settings.certificate_workflow_mail_intake_imap_user,
            settings.certificate_workflow_mail_intake_imap_pass,
        )
        status, _ = imap.select(mailbox)
        if status != "OK":
            return MailIntakeHealth(
                enabled=True,
                imap_host=host,
                imap_port=port,
                mailbox=mailbox,
                use_ssl=use_ssl,
                can_connect=False,
                error=f"imap_select_failed:{status}",
            )
        return MailIntakeHealth(
            enabled=True,
            imap_host=host,
            imap_port=port,
            mailbox=mailbox,
            use_ssl=use_ssl,
            can_connect=True,
            error=None,
        )
    except Exception as exc:  # noqa: BLE001
        return MailIntakeHealth(
            enabled=True,
            imap_host=host,
            imap_port=port,
            mailbox=mailbox,
            use_ssl=use_ssl,
            can_connect=False,
            error=str(exc),
        )
    finally:
        try:
            imap.close()  # type: ignore[name-defined]
        except Exception:
            pass
        try:
            imap.logout()  # type: ignore[name-defined]
        except Exception:
            pass
