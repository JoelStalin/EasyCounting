"""Add indexes for usage records and invoice track ID

Revision ID: 20260207_0001
Revises: 20260206_0003
Create Date: 2026-02-07
"""

from __future__ import annotations

from alembic import op

revision = "20260207_0001"
down_revision = "20260206_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_invoices_track_id", "invoices", ["track_id"])
    op.create_index("ix_usage_records_tenant_fecha", "billing_usage_records", ["tenant_id", "fecha"])
    op.create_index("ix_usage_records_track_id", "billing_usage_records", ["track_id"])


def downgrade() -> None:
    op.drop_index("ix_usage_records_track_id", table_name="billing_usage_records")
    op.drop_index("ix_usage_records_tenant_fecha", table_name="billing_usage_records")
    op.drop_index("ix_invoices_track_id", table_name="invoices")
