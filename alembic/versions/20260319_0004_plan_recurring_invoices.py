"""Add recurring invoice entitlement to billing plans.

Revision ID: 20260319_0004
Revises: 20260319_0003
Create Date: 2026-03-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260319_0004"
down_revision = "20260319_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "billing_plans",
        sa.Column("includes_recurring_invoices", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE billing_plans
            SET includes_recurring_invoices = :enabled
            WHERE lower(name) IN ('profesional', 'professional', 'pro', 'enterprise')
            """
        ),
        {"enabled": True},
    )
    op.alter_column("billing_plans", "includes_recurring_invoices", server_default=None)


def downgrade() -> None:
    op.drop_column("billing_plans", "includes_recurring_invoices")
