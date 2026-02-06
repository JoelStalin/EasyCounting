"""Add billing plans and tenant plan_id

Revision ID: 20260206_0001
Revises: 20240510_0001
Create Date: 2026-02-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260206_0001"
down_revision = "20240510_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("precio_mensual", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("precio_por_documento", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("documentos_incluidos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("name", name="uq_billing_plans_name"),
    )

    op.add_column("tenants", sa.Column("plan_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_tenants_plan_id",
        "tenants",
        "billing_plans",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "billing_usage_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("billing_plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ecf_type", sa.String(length=6), nullable=False),
        sa.Column("track_id", sa.String(length=64), nullable=True),
        sa.Column("monto_cargado", sa.Numeric(16, 4), nullable=False, server_default="0"),
        sa.Column("fecha", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_billing_usage_records_tenant", "billing_usage_records", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_billing_usage_records_tenant", table_name="billing_usage_records")
    op.drop_table("billing_usage_records")

    op.drop_constraint("fk_tenants_plan_id", "tenants", type_="foreignkey")
    op.drop_column("tenants", "plan_id")

    op.drop_table("billing_plans")
