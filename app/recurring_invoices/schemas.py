from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RecurringFrequency = Literal["daily", "biweekly", "monthly", "custom"]
RecurringStatus = Literal["active", "paused", "completed", "cancelled"]


class RecurringInvoiceScheduleCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    frequency: RecurringFrequency
    custom_interval_days: int | None = Field(default=None, ge=2, le=365, alias="customIntervalDays")
    start_at: datetime = Field(alias="startAt")
    end_at: datetime | None = Field(default=None, alias="endAt")
    tipo_ecf: str = Field(..., min_length=3, max_length=3, alias="tipoEcf")
    rnc_receptor: str | None = Field(default=None, min_length=9, max_length=11, alias="rncReceptor")
    total: Decimal = Field(..., gt=0)
    notes: str | None = Field(default=None, max_length=512)

    model_config = ConfigDict(populate_by_name=True)


class RecurringInvoiceScheduleUpdateRequest(RecurringInvoiceScheduleCreateRequest):
    status: RecurringStatus | None = None


class RecurringInvoiceExecutionItem(BaseModel):
    id: int
    invoice_id: int | None = Field(default=None, alias="invoiceId")
    scheduled_for: datetime = Field(alias="scheduledFor")
    executed_at: datetime = Field(alias="executedAt")
    status: str
    error_message: str | None = Field(default=None, alias="errorMessage")

    model_config = ConfigDict(populate_by_name=True)


class RecurringInvoiceScheduleItem(BaseModel):
    id: int
    name: str
    status: RecurringStatus
    frequency: RecurringFrequency
    custom_interval_days: int | None = Field(default=None, alias="customIntervalDays")
    start_at: datetime = Field(alias="startAt")
    end_at: datetime | None = Field(default=None, alias="endAt")
    next_run_at: datetime | None = Field(default=None, alias="nextRunAt")
    last_run_at: datetime | None = Field(default=None, alias="lastRunAt")
    tipo_ecf: str = Field(alias="tipoEcf")
    rnc_receptor: str | None = Field(default=None, alias="rncReceptor")
    total: Decimal
    notes: str | None = None
    last_generated_invoice_id: int | None = Field(default=None, alias="lastGeneratedInvoiceId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    executions: list[RecurringInvoiceExecutionItem] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class RecurringInvoiceRunSummary(BaseModel):
    processed: int
    generated: int
    failed: int
    schedules: list[RecurringInvoiceScheduleItem] = Field(default_factory=list)
