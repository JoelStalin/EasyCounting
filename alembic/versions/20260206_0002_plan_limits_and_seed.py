"""Add plan limit columns, invoice rnc_receptor and seed default plans

Revision ID: 20260206_0002
Revises: 20260206_0001
Create Date: 2026-02-06
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from alembic import op
import sqlalchemy as sa


revision = "20260206_0002"
down_revision = "20260206_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "billing_plans",
        sa.Column("max_facturas_mes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "billing_plans",
        sa.Column("max_facturas_por_receptor_mes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "billing_plans",
        sa.Column("max_monto_por_factura", sa.Numeric(16, 2), nullable=False, server_default="0"),
    )

    op.add_column("invoices", sa.Column("rnc_receptor", sa.String(length=11), nullable=True))
    op.create_index("ix_invoices_rnc_receptor", "invoices", ["rnc_receptor"])

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    bind = op.get_bind()
    existing_names = {
        str(row[0])
        for row in bind.execute(sa.text("SELECT name FROM billing_plans")).fetchall()
    }
    plans_table = sa.table(
        "billing_plans",
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
        sa.column("name", sa.String()),
        sa.column("precio_mensual", sa.Numeric(12, 2)),
        sa.column("precio_por_documento", sa.Numeric(12, 4)),
        sa.column("documentos_incluidos", sa.Integer()),
        sa.column("max_facturas_mes", sa.Integer()),
        sa.column("max_facturas_por_receptor_mes", sa.Integer()),
        sa.column("max_monto_por_factura", sa.Numeric(16, 2)),
        sa.column("descripcion", sa.String()),
    )

    seed_rows = [
        {
            "created_at": now,
            "updated_at": now,
            "name": "Emprendedor",
            "precio_mensual": Decimal("1500.00"),
            "precio_por_documento": Decimal("4.0000"),
            "documentos_incluidos": 500,
            "max_facturas_mes": 500,
            "max_facturas_por_receptor_mes": 10,
            "max_monto_por_factura": Decimal("5000.00"),
            "descripcion": "Plan básico para micro/pequeños contribuyentes.",
        },
        {
            "created_at": now,
            "updated_at": now,
            "name": "PyME",
            "precio_mensual": Decimal("2500.00"),
            "precio_por_documento": Decimal("3.5000"),
            "documentos_incluidos": 1500,
            "max_facturas_mes": 1500,
            "max_facturas_por_receptor_mes": 50,
            "max_monto_por_factura": Decimal("20000.00"),
            "descripcion": "Plan para pymes con volumen medio.",
        },
        {
            "created_at": now,
            "updated_at": now,
            "name": "Profesional",
            "precio_mensual": Decimal("4500.00"),
            "precio_por_documento": Decimal("3.0000"),
            "documentos_incluidos": 5000,
            "max_facturas_mes": 5000,
            "max_facturas_por_receptor_mes": 200,
            "max_monto_por_factura": Decimal("50000.00"),
            "descripcion": "Plan para empresas con alto volumen.",
        },
        {
            "created_at": now,
            "updated_at": now,
            "name": "Enterprise",
            "precio_mensual": Decimal("7500.00"),
            "precio_por_documento": Decimal("2.5000"),
            "documentos_incluidos": 20000,
            "max_facturas_mes": 20000,
            "max_facturas_por_receptor_mes": 1000,
            "max_monto_por_factura": Decimal("200000.00"),
            "descripcion": "Plan para corporativos e integraciones avanzadas.",
        },
    ]

    rows_to_insert = [row for row in seed_rows if row["name"] not in existing_names]
    if rows_to_insert:
        op.bulk_insert(plans_table, rows_to_insert)


def downgrade() -> None:
    op.drop_index("ix_invoices_rnc_receptor", table_name="invoices")
    op.drop_column("invoices", "rnc_receptor")

    op.drop_column("billing_plans", "max_monto_por_factura")
    op.drop_column("billing_plans", "max_facturas_por_receptor_mes")
    op.drop_column("billing_plans", "max_facturas_mes")
