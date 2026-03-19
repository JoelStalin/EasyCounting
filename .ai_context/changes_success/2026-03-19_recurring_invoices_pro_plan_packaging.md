# Cambio aplicado: facturas recurrentes solo desde Pro

Fecha: 2026-03-19

## Resultado

- Se agregó `includes_recurring_invoices` a `billing_plans`.
- El backend bloquea creación, reanudación y ejecución manual de facturas recurrentes cuando el tenant no tiene la capacidad habilitada.
- En ejecución batch, las programaciones activas de tenants sin entitlement se pausan y registran una ejecución fallida en vez de romper el proceso.
- El portal cliente muestra claramente si la funcionalidad está incluida en el plan.
- La vista de recurrentes ahora muestra un bloqueo comercial con CTA a `Planes` cuando el tenant está en plan básico.
- El editor de planes en admin ya permite marcar si un plan incluye facturas recurrentes.
- El seed demo quedó alineado con la política:
  - `Emprendedor`: sin recurrentes
  - `Profesional`: con recurrentes

## Archivos clave

- `app/models/billing.py`
- `alembic/versions/20260319_0004_plan_recurring_invoices.py`
- `app/application/recurring_invoices.py`
- `frontend/apps/client-portal/src/pages/RecurringInvoices.tsx`
- `frontend/apps/client-portal/src/pages/Plans.tsx`
- `frontend/apps/admin-portal/src/pages/PlanEditor.tsx`
- `scripts/automation/seed_public_demo_data.py`
