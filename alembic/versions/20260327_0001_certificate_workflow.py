"""Certificate workflow persistence tables.

Revision ID: 20260327_0001
Revises: 20260325_0001
Create Date: 2026-03-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "20260327_0001"
down_revision = "20260325_0001"
branch_labels = None
depends_on = None


def _inspector():
    return inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(index["name"] == index_name for index in _inspector().get_indexes(table_name))


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(column["name"] == column_name for column in _inspector().get_columns(table_name))


def _drop_table_if_exists(table_name: str) -> None:
    if _has_table(table_name):
        op.drop_table(table_name)


def _json_type():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def upgrade() -> None:
    json_type = _json_type()

    if not _has_table("psc_requests"):
        op.create_table(
            "psc_requests",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("case_id", sa.String(length=50), nullable=False),
            sa.Column("rnc", sa.String(length=20), nullable=False),
            sa.Column("razon_social", sa.String(length=255), nullable=False),
            sa.Column("delegado_nombre", sa.String(length=255), nullable=False),
            sa.Column("delegado_identificacion", sa.String(length=50), nullable=False),
            sa.Column("psc_code", sa.String(length=50), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("owner_email", sa.String(length=255), nullable=True),
            sa.Column("secret_ref", sa.String(length=255), nullable=True),
            sa.Column("payload_json", json_type, nullable=False, server_default=sa.text("'{}'")),
            sa.UniqueConstraint("case_id", name="uq_psc_requests_case_id"),
        )
    elif not _has_column("psc_requests", "secret_ref"):
        with op.batch_alter_table("psc_requests") as batch_op:
            batch_op.add_column(sa.Column("secret_ref", sa.String(length=255), nullable=True))

    if not _has_index("psc_requests", "ix_psc_requests_status"):
        op.create_index("ix_psc_requests_status", "psc_requests", ["status"], unique=False)
    if not _has_index("psc_requests", "ix_psc_requests_rnc"):
        op.create_index("ix_psc_requests_rnc", "psc_requests", ["rnc"], unique=False)

    if not _has_table("workflow_events"):
        op.create_table(
            "workflow_events",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("psc_request_id", sa.Integer(), sa.ForeignKey("psc_requests.id", ondelete="CASCADE"), nullable=False),
            sa.Column("case_id", sa.String(length=50), nullable=False),
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("event_payload", json_type, nullable=False, server_default=sa.text("'{}'")),
        )

    if not _has_index("workflow_events", "ix_workflow_events_case_id"):
        op.create_index("ix_workflow_events_case_id", "workflow_events", ["case_id"], unique=False)
    if not _has_index("workflow_events", "ix_workflow_events_event_type"):
        op.create_index("ix_workflow_events_event_type", "workflow_events", ["event_type"], unique=False)

    if not _has_table("certificate_validations"):
        op.create_table(
            "certificate_validations",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("psc_request_id", sa.Integer(), sa.ForeignKey("psc_requests.id", ondelete="CASCADE"), nullable=False),
            sa.Column("case_id", sa.String(length=50), nullable=False),
            sa.Column("file_name", sa.String(length=255), nullable=False),
            sa.Column("sha256", sa.String(length=64), nullable=False),
            sa.Column("subject", sa.Text(), nullable=True),
            sa.Column("serial_number", sa.String(length=255), nullable=True),
            sa.Column("not_before", sa.DateTime(), nullable=True),
            sa.Column("not_after", sa.DateTime(), nullable=True),
            sa.Column("has_private_key", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("password_ok", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("valid", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("error", sa.Text(), nullable=True),
        )

    if not _has_index("certificate_validations", "ix_certificate_validations_case_id"):
        op.create_index("ix_certificate_validations_case_id", "certificate_validations", ["case_id"], unique=False)
    if not _has_index("certificate_validations", "ix_certificate_validations_valid"):
        op.create_index("ix_certificate_validations_valid", "certificate_validations", ["valid"], unique=False)

    if not _has_table("workflow_reminders"):
        op.create_table(
            "workflow_reminders",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("psc_request_id", sa.Integer(), sa.ForeignKey("psc_requests.id", ondelete="CASCADE"), nullable=False),
            sa.Column("case_id", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("due_at", sa.DateTime(), nullable=False),
            sa.Column("resolved_at", sa.DateTime(), nullable=True),
            sa.Column("metadata_json", json_type, nullable=False, server_default=sa.text("'{}'")),
        )
    if not _has_index("workflow_reminders", "ix_workflow_reminders_due_at"):
        op.create_index("ix_workflow_reminders_due_at", "workflow_reminders", ["due_at"], unique=False)
    if not _has_index("workflow_reminders", "ix_workflow_reminders_status"):
        op.create_index("ix_workflow_reminders_status", "workflow_reminders", ["status"], unique=False)


def downgrade() -> None:
    _drop_table_if_exists("workflow_reminders")
    _drop_table_if_exists("certificate_validations")
    _drop_table_if_exists("workflow_events")
    _drop_table_if_exists("psc_requests")
