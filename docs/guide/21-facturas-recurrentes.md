# Facturas recurrentes

El portal cliente ahora permite programar facturas recurrentes por tenant.

## Disponibilidad por plan

- `Emprendedor / Basico`: no incluido
- `Profesional / Pro`: incluido
- `Enterprise`: incluido

La decision de empaquetarlo desde `Pro` responde a que la recurrencia es una automatizacion operativa, no una capacidad minima de emision.

## Periodos soportados

- diario
- quincenal
- mensual
- personalizado por intervalo en dias

## Flujo

1. Entrar al portal cliente.
2. Ir a `Recurrentes`.
3. Crear la programacion con:
   - nombre interno
   - frecuencia
   - inicio
   - fin opcional
   - tipo e-CF
   - RNC receptor opcional
   - monto total
   - notas
4. La plataforma guarda la programacion y calcula `nextRunAt`.
5. El runner de recurrencia procesa las programaciones vencidas automaticamente.
6. Tambien se puede forzar la ejecucion manual con `Ejecutar vencidas ahora`.

## Endpoints

```text
GET    /api/v1/cliente/recurring-invoices
POST   /api/v1/cliente/recurring-invoices
PUT    /api/v1/cliente/recurring-invoices/{schedule_id}
POST   /api/v1/cliente/recurring-invoices/{schedule_id}/pause
POST   /api/v1/cliente/recurring-invoices/{schedule_id}/resume
POST   /api/v1/cliente/recurring-invoices/run-due
```

## Reglas

- solo aplica a tenants con onboarding fiscal completo
- solo aplica a planes con `includes_recurring_invoices = true`
- una programacion pausada no genera facturas hasta reanudarse
- si el rango termina, la programacion pasa a `completed`
- cada ejecucion crea un `Invoice` con estado `PROGRAMADA_GENERADA`
- el historial corto de ejecuciones queda visible en la misma vista

## Configuracion

Variables:

```text
RECURRING_INVOICE_JOB_ENABLED=true
RECURRING_INVOICE_POLL_SECONDS=60
```
