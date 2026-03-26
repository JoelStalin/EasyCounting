# DGII Flow Audit

## Estado detectado al inicio

- Existía cliente DGII real en `app/dgii/client.py`.
- Existían routers reales en `app/routers/recepcion.py`, `auth.py`, `rfce.py`, `anulacion.py`, `aprobacion.py`, `acuse.py`.
- El problema operativo estaba en `app/main.py`: las rutas legacy compat de `app/api/routes/dgii.py` seguían resolviendo `/api/dgii/recepcion/ecf` con `trackId` local fake.

## Síntoma reproducible inicial

- Las pruebas nuevas recibían `LOCAL-*` en vez de `TRACK-001`.
- El pipeline durable no se ejercitaba a través de la ruta pública esperada.

## Corrección aplicada

- Montaje explícito de routers DGII reales antes de `api_router`.
- Conservación de compatibilidad legacy sin permitir que opaque el flujo real.

## Flujo final

- Auth DGII: `/api/v1/dgii/auth/token`
- Recepción e-CF: `/api/v1/dgii/recepcion/ecf`
- Estado: `/api/v1/dgii/recepcion/status/{track_id}`
- Operaciones: `/api/v1/operations/*`
