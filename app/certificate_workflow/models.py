from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WorkflowStatus(StrEnum):
    DRAFT = "DRAFT"
    INTAKE_COMPLETED = "INTAKE_COMPLETED"
    PRECHECK_FAILED = "PRECHECK_FAILED"
    PRECHECK_OK = "PRECHECK_OK"
    PSC_SELECTED = "PSC_SELECTED"
    HUMAN_SUBMISSION_PENDING = "HUMAN_SUBMISSION_PENDING"
    HUMAN_SUBMISSION_DONE = "HUMAN_SUBMISSION_DONE"
    PSC_UNDER_REVIEW = "PSC_UNDER_REVIEW"
    PSC_NEEDS_CORRECTION = "PSC_NEEDS_CORRECTION"
    PSC_APPROVED = "PSC_APPROVED"
    CERTIFICATE_RECEIVED = "CERTIFICATE_RECEIVED"
    CERTIFICATE_VALIDATION_FAILED = "CERTIFICATE_VALIDATION_FAILED"
    CERTIFICATE_VALIDATED = "CERTIFICATE_VALIDATED"
    SECRET_STORED = "SECRET_STORED"
    SMOKE_TEST_FAILED = "SMOKE_TEST_FAILED"
    READY_FOR_DGII = "READY_FOR_DGII"
    IN_PRODUCTION_USE = "IN_PRODUCTION_USE"
    RENEWAL_PENDING = "RENEWAL_PENDING"
    RENEWED = "RENEWED"


@dataclass(slots=True)
class IntakePayload:
    rnc: str
    razon_social: str
    tipo_contribuyente: str
    delegado_nombre: str
    delegado_identificacion: str
    delegado_correo: str
    delegado_telefono: str
    delegado_cargo: str
    psc_preferida: str
    usa_facturador_gratuito: bool
    ofv_habilitada: bool
    alta_ncf_habilitada: bool
    responsable_ti: str
    responsable_fiscal: str
    ambiente_objetivo: str
    stack_tecnico: str = ""
    repositorio: str = ""
    secret_manager: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WorkflowCase:
    case_id: str
    status: WorkflowStatus
    payload: IntakePayload


@dataclass(slots=True)
class PrecheckResult:
    case_id: str
    status: WorkflowStatus
    errors: list[str]
    warnings: list[str]
    next_actions: list[str]

