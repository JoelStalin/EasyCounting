from __future__ import annotations

from datetime import datetime, timezone

from app.models.fiscal_operation import DGIIAttempt, FiscalOperation


class DgiiSubmissionRepository:
    """Persist DGII submission attempts and tracking state."""

    def __init__(self, db_session):
        self.db = db_session

    def persist_submission(self, operation: FiscalOperation, endpoint: str, payload_hash: str, response: dict, track_id: str | None) -> DGIIAttempt:
        attempt = DGIIAttempt(
            operation_fk=operation.id,
            attempt_no=len(operation.dgii_attempts) + 1,
            endpoint=endpoint,
            status="SUCCESS" if track_id else "FAILED",
            request_payload_hash=payload_hash,
            immediate_response_json=response,
            track_id=track_id,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        self.db.add(attempt)
        operation.dgii_track_id = track_id
        self.db.flush()
        return attempt
