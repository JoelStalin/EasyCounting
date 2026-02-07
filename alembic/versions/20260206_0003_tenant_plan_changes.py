"""Add pending plan change fields to tenants

Revision ID: 20260206_0003
Revises: 20260206_0002
Create Date: 2026-02-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260206_0003"
down_revision = "20260206_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("pending_plan_id", sa.Integer(), nullable=True))
    op.add_column("tenants", sa.Column("plan_change_requested_at", sa.DateTime(), nullable=True))
    op.add_column("tenants", sa.Column("plan_change_effective_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_tenants_pending_plan",
        "tenants",
        "billing_plans",
        ["pending_plan_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_tenants_pending_plan", "tenants", type_="foreignkey")
    op.drop_column("tenants", "plan_change_effective_at")
    op.drop_column("tenants", "plan_change_requested_at")
    op.drop_column("tenants", "pending_plan_id")
