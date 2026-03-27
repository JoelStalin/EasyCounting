"""Workflow execution checkpointing tables.

Revision ID: 20260327_0002
Revises: 20260327_0001
Create Date: 2026-03-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "20260327_0002"
down_revision = "20260327_0001"
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
    if not _has_table("workflow_executions"):
        op.create_table(
            "workflow_executions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("psc_request_id", sa.Integer(), sa.ForeignKey("psc_requests.id", ondelete="CASCADE"), nullable=False),
            sa.Column("case_id", sa.String(length=50), nullable=False),
            sa.Column("execution_id", sa.String(length=80), nullable=False),
            sa.Column("current_step", sa.String(length=80), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("last_success_step", sa.String(length=80), nullable=True),
            sa.Column("resume_token", sa.String(length=120), nullable=True),
            sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("ended_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("execution_id", name="uq_workflow_executions_execution_id"),
        )
    if not _has_index("workflow_executions", "ix_workflow_executions_case_id"):
        op.create_index("ix_workflow_executions_case_id", "workflow_executions", ["case_id"], unique=False)
    if not _has_index("workflow_executions", "ix_workflow_executions_status"):
        op.create_index("ix_workflow_executions_status", "workflow_executions", ["status"], unique=False)

    if not _has_table("workflow_step_logs"):
        op.create_table(
            "workflow_step_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column(
                "workflow_execution_id",
                sa.Integer(),
                sa.ForeignKey("workflow_executions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("execution_id", sa.String(length=80), nullable=False),
            sa.Column("step", sa.String(length=80), nullable=False),
            sa.Column("action", sa.String(length=120), nullable=False),
            sa.Column("result", sa.String(length=40), nullable=False),
            sa.Column("error_code", sa.String(length=80), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("screenshot_path", sa.Text(), nullable=True),
            sa.Column("artifact_path", sa.Text(), nullable=True),
            sa.Column("details_json", json_type, nullable=False, server_default=sa.text("'{}'")),
        )
    if not _has_index("workflow_step_logs", "ix_workflow_step_logs_execution_id"):
        op.create_index("ix_workflow_step_logs_execution_id", "workflow_step_logs", ["execution_id"], unique=False)
    if not _has_index("workflow_step_logs", "ix_workflow_step_logs_step"):
        op.create_index("ix_workflow_step_logs_step", "workflow_step_logs", ["step"], unique=False)


def downgrade() -> None:
    _drop_table_if_exists("workflow_step_logs")
    _drop_table_if_exists("workflow_executions")
