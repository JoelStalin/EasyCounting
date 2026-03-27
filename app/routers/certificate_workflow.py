from __future__ import annotations

import base64
import asyncio
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.certificate_workflow.certificate_validation import validate_p12_file
from app.certificate_workflow.models import IntakePayload, WorkflowStatus
from app.certificate_workflow.notifications import notify_reminder_due
from app.certificate_workflow.persistence import CertificateWorkflowRepository
from app.certificate_workflow.secrets import SecretStoreError, store_certificate_secret
from app.certificate_workflow.track_polling_service import process_ready_cases_track_poll
from app.certificate_workflow.schemas import (
    CaseDetailResponse,
    CertificateValidationResponse,
    DgiiCertificationCheckResponse,
    DgiiSubmitTestResponse,
    DgiiTrackPollResponse,
    DgiiTrackStatusResponse,
    IntakeRequest,
    PrecheckResponse,
    ReminderCreateRequest,
    ReminderItemResponse,
    SmokeSignResponse,
    SecretStoreResponse,
    StatusTransitionRequest,
    WorkflowCheckpointRequest,
    WorkflowExecutionStartResponse,
    WorkflowProgressResponse,
    WorkflowEventResponse,
)
from app.dgii.client import DGIIClient
from app.certificate_workflow.service import build_case_artifacts, create_workflow_case, run_precheck
from app.infra.settings import settings
from app.security.signing import sign_xml_enveloped, validate_signed_xml_details
from app.shared.database import get_db

router = APIRouter(prefix="/certificate-workflow", tags=["certificate-workflow"], include_in_schema=False)

ALLOWED_TRANSITIONS: dict[WorkflowStatus, set[WorkflowStatus]] = {
    WorkflowStatus.INTAKE_COMPLETED: {WorkflowStatus.PRECHECK_FAILED, WorkflowStatus.PRECHECK_OK},
    WorkflowStatus.PRECHECK_FAILED: {WorkflowStatus.PRECHECK_OK},
    WorkflowStatus.PRECHECK_OK: {WorkflowStatus.PSC_SELECTED, WorkflowStatus.HUMAN_SUBMISSION_PENDING},
    WorkflowStatus.PSC_SELECTED: {WorkflowStatus.HUMAN_SUBMISSION_PENDING},
    WorkflowStatus.HUMAN_SUBMISSION_PENDING: {WorkflowStatus.HUMAN_SUBMISSION_DONE, WorkflowStatus.PSC_UNDER_REVIEW},
    WorkflowStatus.HUMAN_SUBMISSION_DONE: {WorkflowStatus.PSC_UNDER_REVIEW},
    WorkflowStatus.PSC_UNDER_REVIEW: {WorkflowStatus.PSC_APPROVED, WorkflowStatus.PSC_NEEDS_CORRECTION},
    WorkflowStatus.PSC_NEEDS_CORRECTION: {WorkflowStatus.HUMAN_SUBMISSION_PENDING, WorkflowStatus.PSC_UNDER_REVIEW},
    WorkflowStatus.PSC_APPROVED: {WorkflowStatus.CERTIFICATE_RECEIVED},
    WorkflowStatus.CERTIFICATE_RECEIVED: {WorkflowStatus.CERTIFICATE_VALIDATED, WorkflowStatus.CERTIFICATE_VALIDATION_FAILED},
    WorkflowStatus.CERTIFICATE_VALIDATION_FAILED: {WorkflowStatus.CERTIFICATE_RECEIVED},
    WorkflowStatus.CERTIFICATE_VALIDATED: {WorkflowStatus.SECRET_STORED, WorkflowStatus.SMOKE_TEST_FAILED},
    WorkflowStatus.SECRET_STORED: {WorkflowStatus.READY_FOR_DGII, WorkflowStatus.SMOKE_TEST_FAILED},
    WorkflowStatus.SMOKE_TEST_FAILED: {WorkflowStatus.CERTIFICATE_VALIDATED, WorkflowStatus.SECRET_STORED},
    WorkflowStatus.READY_FOR_DGII: {WorkflowStatus.IN_PRODUCTION_USE},
    WorkflowStatus.IN_PRODUCTION_USE: {WorkflowStatus.RENEWAL_PENDING},
    WorkflowStatus.RENEWAL_PENDING: {WorkflowStatus.RENEWED},
    WorkflowStatus.RENEWED: {WorkflowStatus.IN_PRODUCTION_USE},
}


def _extract_first(payload: dict, keys: list[str], default: str | None = None) -> str | None:
    for key in keys:
        if key in payload and payload[key] is not None:
            return str(payload[key])
    return default


def _extract_track_id(repo: CertificateWorkflowRepository, case_id: str) -> str | None:
    events = repo.list_events(case_id)
    for event in reversed(events):
        payload = event.event_payload or {}
        track_id = payload.get("track_id") or payload.get("trackId") or payload.get("track")
        if track_id:
            return str(track_id)
    return None


def _normalize_dgii_status(raw: str | None) -> str:
    value = (raw or "").strip().upper().replace(" ", "_")
    return value or "DESCONOCIDO"


def _is_terminal_dgii_status(status_value: str) -> bool:
    return status_value in {"ACEPTADO", "RECHAZADO", "ACEPTADO_CONDICIONAL"}


def _require_internal_secret(
    x_internal_secret: str | None = Header(default=None, alias="X-Internal-Secret"),
) -> None:
    if x_internal_secret != settings.hmac_service_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Internal secret invalido")


@router.post("/intake", response_model=PrecheckResponse)
def create_intake(
    body: IntakeRequest,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> PrecheckResponse:
    payload = IntakePayload(**body.model_dump())
    workflow_case = create_workflow_case(payload)
    precheck = run_precheck(workflow_case)
    case_dir = build_case_artifacts(
        workflow_case,
        precheck,
        base_dir=Path(settings.psc_workflow_storage_path),
    )

    repo = CertificateWorkflowRepository(db)
    row = repo.create_request(
        case_id=workflow_case.case_id,
        payload=workflow_case.payload,
        status_value=precheck.status,
    )
    repo.append_event(
        request_row=row,
        event_type=WorkflowStatus.INTAKE_COMPLETED.value,
        payload={"case_id": workflow_case.case_id},
    )
    repo.append_event(
        request_row=row,
        event_type=precheck.status.value,
        payload={
            "errors": precheck.errors,
            "warnings": precheck.warnings,
            "next_actions": precheck.next_actions,
        },
    )
    db.flush()

    return PrecheckResponse(
        case_id=precheck.case_id,
        status=precheck.status.value,
        errors=precheck.errors,
        warnings=precheck.warnings,
        next_actions=precheck.next_actions,
        case_dir=str(case_dir),
    )


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> CaseDetailResponse:
    repo = CertificateWorkflowRepository(db)
    row = repo.get_request(case_id)
    events = [
        WorkflowEventResponse(
            id=item.id,
            event_type=item.event_type,
            event_payload=item.event_payload,
            created_at=item.created_at.isoformat(),
        )
        for item in repo.list_events(case_id)
    ]
    return CaseDetailResponse(
        case_id=row.case_id,
        status=row.status,
        rnc=row.rnc,
        razon_social=row.razon_social,
        delegado_nombre=row.delegado_nombre,
        psc_code=row.psc_code,
        owner_email=row.owner_email,
        events=events,
    )


@router.post("/{case_id}/validate-certificate", response_model=CertificateValidationResponse)
def validate_certificate(
    case_id: str,
    certificate: UploadFile = File(...),
    password: str = Form(...),
    expected_subject: str | None = Form(default=None),
    expected_serial: str | None = Form(default=None),
    expected_rnc: str | None = Form(default=None),
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> CertificateValidationResponse:
    repo = CertificateWorkflowRepository(db)
    request_row = repo.get_request(case_id)

    suffix = Path(certificate.filename or "cert.p12").suffix or ".p12"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(certificate.file.read())
        tmp_path = Path(tmp.name)
    try:
        result = validate_p12_file(
            file_path=tmp_path,
            password=password,
            expected_subject=expected_subject,
            expected_serial=expected_serial,
            expected_rnc=expected_rnc,
        )
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    parsed_not_before = datetime.fromisoformat(result.not_before) if result.not_before else None
    parsed_not_after = datetime.fromisoformat(result.not_after) if result.not_after else None
    status_value = WorkflowStatus.CERTIFICATE_VALIDATED if result.valid else WorkflowStatus.CERTIFICATE_VALIDATION_FAILED
    repo.create_validation(
        case_id=case_id,
        file_name=certificate.filename or "certificate.p12",
        sha256=result.sha256 or "",
        subject=result.subject,
        serial_number=result.serial_number,
        not_before=parsed_not_before,
        not_after=parsed_not_after,
        has_private_key=result.has_private_key,
        password_ok=result.password_ok,
        valid=result.valid,
        error=result.error,
    )
    request_row.status = status_value.value
    repo.append_event(
        request_row=request_row,
        event_type=status_value.value,
        payload={
            "file_name": certificate.filename or "certificate.p12",
            "valid": result.valid,
            "error": result.error,
            "sha256": result.sha256,
        },
    )
    db.flush()
    return CertificateValidationResponse(
        case_id=case_id,
        validation_status="VALID" if result.valid else "INVALID",
        subject=result.subject,
        serial_number=result.serial_number,
        not_before=result.not_before,
        not_after=result.not_after,
        has_private_key=result.has_private_key,
        fingerprint_sha1=result.fingerprint_sha1,
        sha256=result.sha256,
        error=result.error,
    )


@router.post("/{case_id}/status", response_model=CaseDetailResponse)
def transition_case_status(
    case_id: str,
    body: StatusTransitionRequest,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> CaseDetailResponse:
    repo = CertificateWorkflowRepository(db)
    row = repo.get_request(case_id)
    try:
        current = WorkflowStatus(row.status)
        target = WorkflowStatus(body.status)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estado invalido") from exc
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transicion no permitida: {current.value} -> {target.value}",
        )
    repo.transition_status(case_id, target_status=target, note=body.note)
    refreshed = repo.get_request(case_id)
    events = [
        WorkflowEventResponse(
            id=item.id,
            event_type=item.event_type,
            event_payload=item.event_payload,
            created_at=item.created_at.isoformat(),
        )
        for item in repo.list_events(case_id)
    ]
    return CaseDetailResponse(
        case_id=refreshed.case_id,
        status=refreshed.status,
        rnc=refreshed.rnc,
        razon_social=refreshed.razon_social,
        delegado_nombre=refreshed.delegado_nombre,
        psc_code=refreshed.psc_code,
        owner_email=refreshed.owner_email,
        events=events,
    )


@router.post("/{case_id}/reminders", response_model=ReminderItemResponse)
def schedule_case_reminder(
    case_id: str,
    body: ReminderCreateRequest,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> ReminderItemResponse:
    reminder = CertificateWorkflowRepository(db).schedule_reminder(
        case_id=case_id,
        title=body.title,
        hours=body.hours,
        metadata=body.metadata,
    )
    return ReminderItemResponse(
        id=reminder.id,
        case_id=reminder.case_id,
        status=reminder.status,
        title=reminder.title,
        due_at=reminder.due_at.isoformat(),
        resolved_at=reminder.resolved_at.isoformat() if reminder.resolved_at else None,
        metadata=reminder.metadata_json,
    )


@router.get("/reminders/due", response_model=list[ReminderItemResponse])
def list_due_reminders(
    limit: int = 50,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> list[ReminderItemResponse]:
    items = CertificateWorkflowRepository(db).due_reminders(limit=limit)
    return [
        ReminderItemResponse(
            id=item.id,
            case_id=item.case_id,
            status=item.status,
            title=item.title,
            due_at=item.due_at.isoformat(),
            resolved_at=item.resolved_at.isoformat() if item.resolved_at else None,
            metadata=item.metadata_json,
        )
        for item in items
    ]


@router.post("/reminders/{reminder_id}/resolve", response_model=ReminderItemResponse)
def resolve_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> ReminderItemResponse:
    item = CertificateWorkflowRepository(db).resolve_reminder(reminder_id)
    return ReminderItemResponse(
        id=item.id,
        case_id=item.case_id,
        status=item.status,
        title=item.title,
        due_at=item.due_at.isoformat(),
        resolved_at=item.resolved_at.isoformat() if item.resolved_at else None,
        metadata=item.metadata_json,
    )


@router.post("/{case_id}/store-secret", response_model=SecretStoreResponse)
def store_certificate_secret_endpoint(
    case_id: str,
    certificate: UploadFile = File(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> SecretStoreResponse:
    repo = CertificateWorkflowRepository(db)
    row = repo.get_request(case_id)
    data = certificate.file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo de certificado vacio")
    metadata = {
        "file_name": certificate.filename or "certificate.p12",
        "rnc": row.rnc,
        "delegado_nombre": row.delegado_nombre,
    }
    try:
        secret_ref = store_certificate_secret(
            case_id=case_id,
            certificate_bytes=data,
            certificate_password=password,
            metadata=metadata,
        )
    except SecretStoreError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    repo.set_secret_ref(case_id=case_id, secret_ref=secret_ref)
    return SecretStoreResponse(case_id=case_id, status=WorkflowStatus.SECRET_STORED.value, secret_ref=secret_ref)


@router.post("/{case_id}/smoke-sign", response_model=SmokeSignResponse)
def smoke_sign_case(
    case_id: str,
    sample_xml_base64: str | None = Form(default=None),
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> SmokeSignResponse:
    from app.certificate_workflow.secrets import load_certificate_secret

    repo = CertificateWorkflowRepository(db)
    row = repo.get_request(case_id)
    if not row.secret_ref:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="case_id sin secret_ref almacenado")
    try:
        payload = load_certificate_secret(row.secret_ref)
    except SecretStoreError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    cert_b64 = str(payload.get("certificate_base64") or "").strip()
    cert_password = str(payload.get("certificate_password") or "").strip()
    if not cert_b64 or not cert_password:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Secreto de certificado incompleto")

    sample_xml = (
        base64.b64decode(sample_xml_base64)
        if sample_xml_base64
        else f"<Postulacion><CaseId>{case_id}</CaseId><RNC>{row.rnc}</RNC></Postulacion>".encode("utf-8")
    )
    sample_hash = hashlib.sha256(sample_xml).hexdigest()
    cert_bytes = base64.b64decode(cert_b64)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".p12") as tmp:
        tmp.write(cert_bytes)
        p12_path = Path(tmp.name)
    try:
        signed_xml = sign_xml_enveloped(sample_xml, str(p12_path), cert_password, reference_uri="")
        valid = validate_signed_xml_details(signed_xml).valid
    finally:
        p12_path.unlink(missing_ok=True)

    if valid:
        repo.transition_status(case_id, target_status=WorkflowStatus.READY_FOR_DGII, note="Smoke sign OK")
    else:
        repo.transition_status(case_id, target_status=WorkflowStatus.SMOKE_TEST_FAILED, note="Smoke sign failed")

    return SmokeSignResponse(
        case_id=case_id,
        status=WorkflowStatus.READY_FOR_DGII.value if valid else WorkflowStatus.SMOKE_TEST_FAILED.value,
        signature_valid=valid,
        sample_hash_sha256=sample_hash,
    )


@router.post("/reminders/process-due")
def process_due_reminders_endpoint(
    limit: int = 50,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> dict[str, int]:
    repo = CertificateWorkflowRepository(db)
    processed = 0
    for item in repo.due_reminders(limit=limit):
        request_row = repo.get_request(item.case_id)
        notify_reminder_due(case_id=item.case_id, title=item.title, owner_email=request_row.owner_email)
        item.status = "OVERDUE_NOTIFIED"
        db.flush()
        repo.append_event(
            request_row=request_row,
            event_type="REMINDER_OVERDUE_NOTIFIED",
            payload={"reminder_id": item.id, "title": item.title},
        )
        processed += 1
    return {"processed": processed}


@router.post("/{case_id}/dgii-certification-check", response_model=DgiiCertificationCheckResponse)
async def dgii_certification_check(
    case_id: str,
    live: bool = False,
    transition_to_in_production: bool = False,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> DgiiCertificationCheckResponse:
    repo = CertificateWorkflowRepository(db)
    row = repo.get_request(case_id)
    if row.status not in {
        WorkflowStatus.READY_FOR_DGII.value,
        WorkflowStatus.SECRET_STORED.value,
        WorkflowStatus.IN_PRODUCTION_USE.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Estado {row.status} no habilitado para verificacion DGII",
        )

    token_obtained = False
    directory_checked = False
    detail = "Verificacion simulada ejecutada"
    mode = "simulated"

    if live:
        mode = "live"
        try:
            async with DGIIClient() as client:
                token = await client.bearer()
                token_obtained = bool(token)
                _ = await client.consulta_directorio(row.rnc, token=token)
                directory_checked = True
                detail = "Token DGII obtenido y consulta directorio ejecutada"
        except Exception as exc:  # noqa: BLE001
            repo.append_event(
                request_row=row,
                event_type="DGII_CERT_CHECK_FAILED",
                payload={"mode": mode, "error": str(exc)},
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Fallo DGII live check: {exc}") from exc

    repo.append_event(
        request_row=row,
        event_type="DGII_CERT_CHECK_OK",
        payload={
            "mode": mode,
            "token_obtained": token_obtained,
            "directory_checked": directory_checked,
            "detail": detail,
        },
    )
    if transition_to_in_production:
        try:
            target = WorkflowStatus.IN_PRODUCTION_USE
            current = WorkflowStatus(row.status)
            allowed = ALLOWED_TRANSITIONS.get(current, set())
            if target in allowed:
                repo.transition_status(case_id, target_status=target, note="DGII certification check completed")
                row = repo.get_request(case_id)
        except Exception:
            pass

    return DgiiCertificationCheckResponse(
        case_id=case_id,
        status=row.status,
        mode=mode,
        token_obtained=token_obtained,
        directory_checked=directory_checked,
        detail=detail,
    )


@router.post("/{case_id}/submit-test-ecf", response_model=DgiiSubmitTestResponse)
async def submit_test_ecf(
    case_id: str,
    sample_xml_base64: str | None = Form(default=None),
    live: bool = False,
    transition_to_in_production: bool = False,
    idempotency_key: str | None = None,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> DgiiSubmitTestResponse:
    from app.certificate_workflow.secrets import load_certificate_secret

    repo = CertificateWorkflowRepository(db)
    row = repo.get_request(case_id)
    if row.status not in {WorkflowStatus.READY_FOR_DGII.value, WorkflowStatus.IN_PRODUCTION_USE.value}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Estado {row.status} no habilitado para submit de prueba",
        )
    if not row.secret_ref:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="case_id sin secret_ref almacenado")

    try:
        payload = load_certificate_secret(row.secret_ref)
    except SecretStoreError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    cert_b64 = str(payload.get("certificate_base64") or "").strip()
    cert_password = str(payload.get("certificate_password") or "").strip()
    if not cert_b64 or not cert_password:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Secreto de certificado incompleto")

    sample_xml = (
        base64.b64decode(sample_xml_base64)
        if sample_xml_base64
        else f"<ECFPrueba><CaseId>{case_id}</CaseId><RNC>{row.rnc}</RNC></ECFPrueba>".encode("utf-8")
    )
    cert_bytes = base64.b64decode(cert_b64)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".p12") as tmp:
        tmp.write(cert_bytes)
        p12_path = Path(tmp.name)
    try:
        signed_xml = sign_xml_enveloped(sample_xml, str(p12_path), cert_password, reference_uri="")
    finally:
        p12_path.unlink(missing_ok=True)

    payload_hash = hashlib.sha256(signed_xml).hexdigest()
    mode = "simulated"
    detail = "Submit de prueba simulado ejecutado"
    track_id = f"SIM-{payload_hash[:16].upper()}"

    if live:
        mode = "live"
        try:
            async with DGIIClient() as client:
                result = await client.send_ecf(signed_xml, idempotency_key=idempotency_key or f"wf-{case_id}")
                track_id = _extract_first(result, ["track_id", "trackId", "track"], track_id) or track_id
                detail = "Submit DGII live ejecutado"
        except Exception as exc:  # noqa: BLE001
            repo.append_event(
                request_row=row,
                event_type="DGII_TEST_SUBMIT_FAILED",
                payload={"mode": mode, "error": str(exc)},
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Fallo DGII live submit: {exc}") from exc

    repo.append_event(
        request_row=row,
        event_type="DGII_TEST_SUBMIT_OK",
        payload={
            "mode": mode,
            "track_id": track_id,
            "detail": detail,
            "signed_xml_sha256": payload_hash,
        },
    )
    repo.append_event(
        request_row=row,
        event_type="DGII_TRACKID_REGISTERED",
        payload={"track_id": track_id},
    )

    if transition_to_in_production:
        try:
            target = WorkflowStatus.IN_PRODUCTION_USE
            current = WorkflowStatus(row.status)
            allowed = ALLOWED_TRANSITIONS.get(current, set())
            if target in allowed:
                repo.transition_status(case_id, target_status=target, note="DGII test submit completed")
                row = repo.get_request(case_id)
        except Exception:
            pass

    return DgiiSubmitTestResponse(
        case_id=case_id,
        status=row.status,
        mode=mode,
        track_id=track_id,
        detail=detail,
    )


@router.get("/{case_id}/track-status", response_model=DgiiTrackStatusResponse)
async def query_track_status(
    case_id: str,
    track_id: str | None = None,
    live: bool = False,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> DgiiTrackStatusResponse:
    repo = CertificateWorkflowRepository(db)
    row = repo.get_request(case_id)
    resolved_track_id = track_id or _extract_track_id(repo, case_id)
    if not resolved_track_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No existe TrackId persistido para este case_id",
        )

    mode = "simulated"
    dgii_status = "EN_PROCESO"
    detail = "Consulta de TrackId simulada"

    if live:
        mode = "live"
        try:
            async with DGIIClient() as client:
                result = await client.get_status(resolved_track_id)
                dgii_status = _normalize_dgii_status(
                    _extract_first(result, ["estado", "status", "respuesta"], "DESCONOCIDO")
                )
                detail = _extract_first(result, ["descripcion", "detalle", "message"], None)
        except Exception as exc:  # noqa: BLE001
            repo.append_event(
                request_row=row,
                event_type="DGII_TRACK_STATUS_FAILED",
                payload={"mode": mode, "track_id": resolved_track_id, "error": str(exc)},
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Fallo DGII live status: {exc}") from exc

    repo.append_event(
        request_row=row,
        event_type="DGII_TRACK_STATUS_OK",
        payload={
            "mode": mode,
            "track_id": resolved_track_id,
            "dgii_status": dgii_status,
            "detail": detail,
        },
    )

    return DgiiTrackStatusResponse(
        case_id=case_id,
        status=row.status,
        mode=mode,
        track_id=resolved_track_id,
        dgii_status=dgii_status,
        detail=detail,
    )


@router.get("/{case_id}/track-status/poll", response_model=DgiiTrackPollResponse)
async def poll_track_status(
    case_id: str,
    track_id: str | None = None,
    live: bool = False,
    max_attempts: int = 3,
    interval_ms: int = 500,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> DgiiTrackPollResponse:
    repo = CertificateWorkflowRepository(db)
    row = repo.get_request(case_id)
    resolved_track_id = track_id or _extract_track_id(repo, case_id)
    if not resolved_track_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No existe TrackId persistido para este case_id",
        )
    if max_attempts < 1 or max_attempts > 20:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="max_attempts debe estar entre 1 y 20")
    if interval_ms < 0 or interval_ms > 60000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="interval_ms fuera de rango")

    mode = "live" if live else "simulated"
    attempts_used = 0
    detail: str | None = None
    dgii_status = "EN_PROCESO"

    for attempt in range(1, max_attempts + 1):
        attempts_used = attempt
        if live:
            try:
                async with DGIIClient() as client:
                    result = await client.get_status(resolved_track_id)
                    dgii_status = _normalize_dgii_status(
                        _extract_first(result, ["estado", "status", "respuesta"], "DESCONOCIDO")
                    )
                    detail = _extract_first(result, ["descripcion", "detalle", "message"], None)
            except Exception as exc:  # noqa: BLE001
                repo.append_event(
                    request_row=row,
                    event_type="DGII_TRACK_POLL_FAILED",
                    payload={"mode": mode, "track_id": resolved_track_id, "attempt": attempt, "error": str(exc)},
                )
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Fallo DGII poll: {exc}") from exc
        else:
            # Simulacion determinista: pasa de EN_PROCESO a ACEPTADO en el ultimo intento.
            dgii_status = "ACEPTADO" if attempt == max_attempts and max_attempts > 1 else "EN_PROCESO"
            detail = f"Polling simulado intento {attempt}/{max_attempts}"

        if _is_terminal_dgii_status(dgii_status):
            break
        if attempt < max_attempts and interval_ms > 0:
            await asyncio.sleep(interval_ms / 1000)

    terminal = _is_terminal_dgii_status(dgii_status)
    repo.append_event(
        request_row=row,
        event_type="DGII_TRACK_POLL_OK",
        payload={
            "mode": mode,
            "track_id": resolved_track_id,
            "attempts_used": attempts_used,
            "dgii_status": dgii_status,
            "terminal": terminal,
            "detail": detail,
        },
    )

    if terminal and dgii_status == "ACEPTADO":
        try:
            target = WorkflowStatus.IN_PRODUCTION_USE
            current = WorkflowStatus(row.status)
            allowed = ALLOWED_TRANSITIONS.get(current, set())
            if target in allowed:
                repo.transition_status(case_id, target_status=target, note="DGII track poll accepted")
                row = repo.get_request(case_id)
        except Exception:
            pass

    return DgiiTrackPollResponse(
        case_id=case_id,
        status=row.status,
        mode=mode,
        track_id=resolved_track_id,
        dgii_status=dgii_status,
        terminal=terminal,
        attempts_used=attempts_used,
        detail=detail,
    )


@router.post("/track-status/process-ready")
async def process_ready_track_status(
    live: bool | None = None,
    limit: int | None = None,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> dict[str, int | str]:
    del db  # endpoint-level DB dependency kept for consistency with internal auth flow.
    effective_live = settings.certificate_workflow_track_poll_live if live is None else live
    effective_limit = settings.certificate_workflow_track_poll_limit if limit is None else limit
    processed = await process_ready_cases_track_poll(limit=effective_limit, live=effective_live)
    return {
        "processed": processed,
        "mode": "live" if effective_live else "simulated",
        "limit": effective_limit,
    }


@router.post("/{case_id}/execution/start", response_model=WorkflowExecutionStartResponse)
def start_workflow_execution(
    case_id: str,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> WorkflowExecutionStartResponse:
    repo = CertificateWorkflowRepository(db)
    row = repo.start_execution(case_id=case_id, current_step="INTAKE_RECEIVED", status_value="RUNNING")
    return WorkflowExecutionStartResponse(
        case_id=case_id,
        execution_id=row.execution_id,
        status=row.status,
        current_step=row.current_step,
        last_success_step=row.last_success_step,
        resume_token=row.resume_token,
        attempt=row.attempt,
    )


@router.post("/{case_id}/checkpoint", response_model=WorkflowExecutionStartResponse)
def log_workflow_checkpoint(
    case_id: str,
    body: WorkflowCheckpointRequest,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> WorkflowExecutionStartResponse:
    repo = CertificateWorkflowRepository(db)
    execution = repo.get_execution(body.execution_id)
    if execution.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="execution_id no pertenece al case_id")
    repo.log_step(
        execution_id=body.execution_id,
        step=body.step,
        action=body.action,
        result=body.result,
        error_code=body.error_code,
        error_message=body.error_message,
        screenshot_path=body.screenshot_path,
        artifact_path=body.artifact_path,
        details=body.details,
    )
    refreshed = repo.get_execution(body.execution_id)
    return WorkflowExecutionStartResponse(
        case_id=case_id,
        execution_id=refreshed.execution_id,
        status=refreshed.status,
        current_step=refreshed.current_step,
        last_success_step=refreshed.last_success_step,
        resume_token=refreshed.resume_token,
        attempt=refreshed.attempt,
    )


@router.get("/{case_id}/progress", response_model=WorkflowProgressResponse)
def get_workflow_progress(
    case_id: str,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> WorkflowProgressResponse:
    repo = CertificateWorkflowRepository(db)
    _ = repo.get_request(case_id)
    execution = repo.latest_execution(case_id)
    if execution is None:
        return WorkflowProgressResponse(
            case_id=case_id,
            execution_id=None,
            status=None,
            current_step=None,
            last_success_step=None,
            resume_token=None,
            attempt=None,
            latest_error_code=None,
            latest_error_message=None,
        )
    logs = repo.list_execution_logs(execution.execution_id, limit=1)
    latest_error_code = None
    latest_error_message = None
    if logs:
        latest_error_code = logs[0].error_code
        latest_error_message = logs[0].error_message
    return WorkflowProgressResponse(
        case_id=case_id,
        execution_id=execution.execution_id,
        status=execution.status,
        current_step=execution.current_step,
        last_success_step=execution.last_success_step,
        resume_token=execution.resume_token,
        attempt=execution.attempt,
        latest_error_code=latest_error_code,
        latest_error_message=latest_error_message,
    )


@router.post("/{case_id}/resume", response_model=WorkflowExecutionStartResponse)
def resume_workflow_case(
    case_id: str,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> WorkflowExecutionStartResponse:
    repo = CertificateWorkflowRepository(db)
    row = repo.resume_latest_execution(case_id)
    return WorkflowExecutionStartResponse(
        case_id=case_id,
        execution_id=row.execution_id,
        status=row.status,
        current_step=row.current_step,
        last_success_step=row.last_success_step,
        resume_token=row.resume_token,
        attempt=row.attempt,
    )
