"""add odoo mirror tables

Revision ID: 20260327_0004
Revises: 20260327_0003
Create Date: 2026-03-27 06:20:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260327_0004"
down_revision = "20260327_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "odoo_partner_mirror",
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("odoo_id", sa.Integer(), nullable=False),
        sa.Column("partner_kind", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("vat", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("company_type", sa.String(length=32), nullable=True),
        sa.Column("raw_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("synced_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "odoo_id", name="ux_odoo_partner_mirror_tenant_odoo"),
    )
    op.create_index("ix_odoo_partner_mirror_odoo_id", "odoo_partner_mirror", ["odoo_id"], unique=False)
    op.create_index("ix_odoo_partner_mirror_tenant_kind", "odoo_partner_mirror", ["tenant_id", "partner_kind"], unique=False)

    op.create_table(
        "odoo_product_mirror",
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("odoo_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("default_code", sa.String(length=64), nullable=True),
        sa.Column("list_price", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("standard_price", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("raw_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("synced_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "odoo_id", name="ux_odoo_product_mirror_tenant_odoo"),
    )
    op.create_index("ix_odoo_product_mirror_odoo_id", "odoo_product_mirror", ["odoo_id"], unique=False)
    op.create_index(
        "ix_odoo_product_mirror_tenant_default_code",
        "odoo_product_mirror",
        ["tenant_id", "default_code"],
        unique=False,
    )

    op.create_table(
        "odoo_invoice_mirror",
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("odoo_id", sa.Integer(), nullable=False),
        sa.Column("move_name", sa.String(length=64), nullable=True),
        sa.Column("move_type", sa.String(length=32), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=True),
        sa.Column("payment_state", sa.String(length=32), nullable=True),
        sa.Column("invoice_date", sa.DateTime(), nullable=True),
        sa.Column("partner_name", sa.String(length=255), nullable=True),
        sa.Column("partner_vat", sa.String(length=32), nullable=True),
        sa.Column("amount_total", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("amount_tax", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("amount_untaxed", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("encf", sa.String(length=20), nullable=True),
        sa.Column("raw_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("lines_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("synced_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "odoo_id", name="ux_odoo_invoice_mirror_tenant_odoo"),
    )
    op.create_index("ix_odoo_invoice_mirror_odoo_id", "odoo_invoice_mirror", ["odoo_id"], unique=False)
    op.create_index("ix_odoo_invoice_mirror_tenant_state", "odoo_invoice_mirror", ["tenant_id", "state"], unique=False)
    op.create_index(
        "ix_odoo_invoice_mirror_tenant_move_name",
        "odoo_invoice_mirror",
        ["tenant_id", "move_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_odoo_invoice_mirror_tenant_move_name", table_name="odoo_invoice_mirror")
    op.drop_index("ix_odoo_invoice_mirror_tenant_state", table_name="odoo_invoice_mirror")
    op.drop_index("ix_odoo_invoice_mirror_odoo_id", table_name="odoo_invoice_mirror")
    op.drop_table("odoo_invoice_mirror")

    op.drop_index("ix_odoo_product_mirror_tenant_default_code", table_name="odoo_product_mirror")
    op.drop_index("ix_odoo_product_mirror_odoo_id", table_name="odoo_product_mirror")
    op.drop_table("odoo_product_mirror")

    op.drop_index("ix_odoo_partner_mirror_tenant_kind", table_name="odoo_partner_mirror")
    op.drop_index("ix_odoo_partner_mirror_odoo_id", table_name="odoo_partner_mirror")
    op.drop_table("odoo_partner_mirror")
