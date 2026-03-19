# 2026-03-19 - Servicio de facturas recurrentes

## Objetivo

Agregar programacion de facturas recurrentes para clientes empresariales desde el portal cliente.

## Backend

- modelos:
  - `RecurringInvoiceSchedule`
  - `RecurringInvoiceExecution`
- migracion:
  - `20260319_0003_recurring_invoices.py`
- servicio:
  - `app/application/recurring_invoices.py`
- runner automatico:
  - `app/jobs/recurring_invoices.py`
- endpoints cliente:
  - listar
  - crear
  - actualizar
  - pausar
  - reanudar
  - ejecutar vencidas

## Frontend

- nueva vista `Recurrentes` en portal cliente
- formulario de programacion
- historial corto de ejecuciones
- accion manual `Ejecutar vencidas ahora`
- tour autoguiado `client-recurring-invoices`

## Periodos soportados

- `daily`
- `biweekly`
- `monthly`
- `custom` con `customIntervalDays`
