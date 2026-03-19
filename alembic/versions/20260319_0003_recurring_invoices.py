"""Add recurring invoice schedules and executions.

Revision ID: 20260319_0003
Revises: 20260319_0002
Create Date: 2026-03-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260319_0003"
down_revision = "20260319_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recurring_invoice_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("last_generated_invoice_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("custom_interval_days", sa.Integer(), nullable=True),
        sa.Column("start_at", sa.DateTime(), nullable=False),
        sa.Column("end_at", sa.DateTime(), nullable=True),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("tipo_ecf", sa.String(length=3), nullable=False),
        sa.Column("rnc_receptor", sa.String(length=11), nullable=True),
        sa.Column("total", sa.Numeric(16, 2), nullable=False),
        sa.Column("notes", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_generated_invoice_id"], ["invoices.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_recurring_invoice_schedules_tenant_status",
        "recurring_invoice_schedules",
        ["tenant_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_recurring_invoice_schedules_next_run_at",
        "recurring_invoice_schedules",
        ["next_run_at"],
        unique=False,
    )

    op.create_table(
        "recurring_invoice_executions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("schedule_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(), nullable=False),
        sa.Column("executed_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="generated"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["schedule_id"], ["recurring_invoice_schedules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("schedule_id", "scheduled_for", name="ux_recurring_invoice_schedule_occurrence"),
    )
    op.create_index(
        "ix_recurring_invoice_executions_tenant_id",
        "recurring_invoice_executions",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_recurring_invoice_executions_scheduled_for",
        "recurring_invoice_executions",
        ["scheduled_for"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_recurring_invoice_executions_scheduled_for", table_name="recurring_invoice_executions")
    op.drop_index("ix_recurring_invoice_executions_tenant_id", table_name="recurring_invoice_executions")
    op.drop_table("recurring_invoice_executions")

    op.drop_index("ix_recurring_invoice_schedules_next_run_at", table_name="recurring_invoice_schedules")
    op.drop_index("ix_recurring_invoice_schedules_tenant_status", table_name="recurring_invoice_schedules")
    op.drop_table("recurring_invoice_schedules")
