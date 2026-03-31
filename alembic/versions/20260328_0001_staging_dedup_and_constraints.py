"""staging dedup audit and performance indexes

Revision ID: 20260328_0001
Revises: 20260327_0005
Create Date: 2026-03-28

Notas de staging:
  Antes de aplicar esta migración en un entorno con datos existentes, ejecutar:
    python scripts/staging_dedup_check.py --dry-run
  para auditar duplicados potenciales en fiscal_operations y invoices.

  Si se detectan duplicados, ejecutar:
    python scripts/staging_dedup_check.py --fix
  para consolidarlos antes de que las restricciones únicas sean aplicadas.

  Los índices únicos ya existen en fiscal_operations (operation_key, operation_id)
  y en invoices (tenant_id, encf). Esta migración agrega índices de rendimiento
  adicionales para las consultas más frecuentes del pipeline DGII/Odoo.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260328_0001"
down_revision = "20260327_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # fiscal_operations: índices de rendimiento para consultas frecuentes
    # -------------------------------------------------------------------------
    # Índice compuesto para filtrado por estado + ambiente (usado en list_operations)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fiscal_operations_env_state "
        "ON fiscal_operations (environment, state)"
    )

    # Índice para dgii_status (consultas de estado DGII)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fiscal_operations_dgii_status "
        "ON fiscal_operations (dgii_status) WHERE dgii_status IS NOT NULL"
    )

    # Índice para odoo_sync_state (consultas de sincronización Odoo)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fiscal_operations_odoo_sync_state "
        "ON fiscal_operations (odoo_sync_state)"
    )

    # Índice para completed_at (consultas de operaciones completadas)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fiscal_operations_completed_at "
        "ON fiscal_operations (completed_at) WHERE completed_at IS NOT NULL"
    )

    # -------------------------------------------------------------------------
    # invoices: índices de rendimiento adicionales
    # -------------------------------------------------------------------------
    # Índice para odoo_sync_state en invoices
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_invoices_odoo_sync_state "
        "ON invoices (odoo_sync_state)"
    )

    # Índice para fecha_emision + tenant_id (consultas de dashboard)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_invoices_tenant_fecha "
        "ON invoices (tenant_id, fecha_emision DESC)"
    )

    # -------------------------------------------------------------------------
    # fiscal_operation_events: índice para SSE stream (consultas por id > last_seen)
    # -------------------------------------------------------------------------
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fiscal_operation_events_occurred_at "
        "ON fiscal_operation_events (operation_fk, occurred_at DESC)"
    )

    # -------------------------------------------------------------------------
    # dgii_attempts: índice para latencia y auditoría
    # -------------------------------------------------------------------------
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_dgii_attempts_status "
        "ON dgii_attempts (status)"
    )

    # -------------------------------------------------------------------------
    # odoo_sync_attempts: índice para estado de sincronización
    # -------------------------------------------------------------------------
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_odoo_sync_attempts_status "
        "ON odoo_sync_attempts (status)"
    )

    # -------------------------------------------------------------------------
    # comprobante_coverage_results: índice para result_status
    # -------------------------------------------------------------------------
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_comprobante_coverage_result_status "
        "ON comprobante_coverage_results (result_status)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_comprobante_coverage_result_status")
    op.execute("DROP INDEX IF EXISTS ix_odoo_sync_attempts_status")
    op.execute("DROP INDEX IF EXISTS ix_dgii_attempts_status")
    op.execute("DROP INDEX IF EXISTS ix_fiscal_operation_events_occurred_at")
    op.execute("DROP INDEX IF EXISTS ix_invoices_tenant_fecha")
    op.execute("DROP INDEX IF EXISTS ix_invoices_odoo_sync_state")
    op.execute("DROP INDEX IF EXISTS ix_fiscal_operations_completed_at")
    op.execute("DROP INDEX IF EXISTS ix_fiscal_operations_odoo_sync_state")
    op.execute("DROP INDEX IF EXISTS ix_fiscal_operations_dgii_status")
    op.execute("DROP INDEX IF EXISTS ix_fiscal_operations_env_state")
