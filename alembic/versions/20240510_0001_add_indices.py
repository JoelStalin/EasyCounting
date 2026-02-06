"""Add indexes for invoices"""

from __future__ import annotations

from alembic import op

revision = "20240510_0001"
down_revision = "20240509_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ux_invoices_tenant_encf", "invoices", ["tenant_id", "encf"], unique=True)
    op.create_index("ix_invoices_estado", "invoices", ["estado_dgii"])


def downgrade() -> None:
    op.drop_index("ix_invoices_estado", table_name="invoices")
    op.drop_index("ux_invoices_tenant_encf", table_name="invoices")
