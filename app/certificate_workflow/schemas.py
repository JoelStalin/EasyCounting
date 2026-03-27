from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class IntakeRequest(BaseModel):
    rnc: str
    razon_social: str
    tipo_contribuyente: str
    delegado_nombre: str
    delegado_identificacion: str
    delegado_correo: str
    delegado_telefono: str
    delegado_cargo: str
    psc_preferida: str
    usa_facturador_gratuito: bool = False
    ofv_habilitada: bool = False
    alta_ncf_habilitada: bool = False
    responsable_ti: str
    responsable_fiscal: str
    ambiente_objetivo: str
    stack_tecnico: str = ""
    repositorio: str = ""
    secret_manager: str = ""
    metadata: dict = Field(default_factory=dict)


class PrecheckResponse(BaseModel):
    case_id: str
    status: str
    errors: list[str]
    warnings: list[str]
    next_actions: list[str]
    case_dir: str


class WorkflowEventResponse(BaseModel):
    id: int
    event_type: str
    event_payload: dict
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class CaseDetailResponse(BaseModel):
    case_id: str
    status: str
    rnc: str
    razon_social: str
    delegado_nombre: str
    psc_code: str | None
    owner_email: str | None
    events: list[WorkflowEventResponse]


class CertificateValidationResponse(BaseModel):
    case_id: str
    validation_status: str
    subject: str | None
    serial_number: str | None
    not_before: str | None
    not_after: str | None
    has_private_key: bool
    fingerprint_sha1: str | None
    sha256: str | None
    error: str | None


class StatusTransitionRequest(BaseModel):
    status: str
    note: str = ""


class ReminderCreateRequest(BaseModel):
    title: str
    hours: int = Field(default=72, ge=1, le=720)
    metadata: dict = Field(default_factory=dict)


class ReminderItemResponse(BaseModel):
    id: int
    case_id: str
    status: str
    title: str
    due_at: str
    resolved_at: str | None
    metadata: dict


class SecretStoreResponse(BaseModel):
    case_id: str
    status: str
    secret_ref: str


class SmokeSignResponse(BaseModel):
    case_id: str
    status: str
    signature_valid: bool
    sample_hash_sha256: str


class DgiiCertificationCheckResponse(BaseModel):
    case_id: str
    status: str
    mode: str
    token_obtained: bool
    directory_checked: bool
    detail: str


class DgiiSubmitTestResponse(BaseModel):
    case_id: str
    status: str
    mode: str
    track_id: str
    detail: str


class DgiiTrackStatusResponse(BaseModel):
    case_id: str
    status: str
    mode: str
    track_id: str
    dgii_status: str
    detail: str | None = None


class DgiiTrackPollResponse(BaseModel):
    case_id: str
    status: str
    mode: str
    track_id: str
    dgii_status: str
    terminal: bool
    attempts_used: int
    detail: str | None = None


class WorkflowExecutionStartResponse(BaseModel):
    case_id: str
    execution_id: str
    status: str
    current_step: str
    last_success_step: str | None
    resume_token: str | None
    attempt: int


class WorkflowCheckpointRequest(BaseModel):
    execution_id: str
    step: str
    action: str
    result: str
    error_code: str | None = None
    error_message: str | None = None
    screenshot_path: str | None = None
    artifact_path: str | None = None
    details: dict = Field(default_factory=dict)


class WorkflowProgressResponse(BaseModel):
    case_id: str
    execution_id: str | None
    status: str | None
    current_step: str | None
    last_success_step: str | None
    resume_token: str | None
    attempt: int | None
    latest_error_code: str | None
    latest_error_message: str | None
