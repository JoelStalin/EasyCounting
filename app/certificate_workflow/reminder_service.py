from __future__ import annotations

from app.certificate_workflow.notifications import notify_reminder_due
from app.certificate_workflow.persistence import CertificateWorkflowRepository
from app.shared.database import session_scope


def process_due_reminders(limit: int = 50) -> int:
    processed = 0
    with session_scope() as session:
        repo = CertificateWorkflowRepository(session)
        due_items = repo.due_reminders(limit=limit)
        for item in due_items:
            request_row = repo.get_request(item.case_id)
            notify_reminder_due(case_id=item.case_id, title=item.title, owner_email=request_row.owner_email)
            item.status = "OVERDUE_NOTIFIED"
            session.flush()
            repo.append_event(
                request_row=request_row,
                event_type="REMINDER_OVERDUE_NOTIFIED",
                payload={"reminder_id": item.id, "title": item.title},
            )
            processed += 1
    return processed

