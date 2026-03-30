# Smoke Checklist Pre-refactor

Fecha: 2026-03-30

## 1. Autenticación
- [ ] `POST /auth/login` con credenciales válidas devuelve token/sesión.
- [ ] `POST /auth/mfa/verify` responde correctamente cuando MFA está activo.
- [ ] `GET /api/v1/me` con token válido devuelve usuario autenticado.

## 2. Endpoints principales
- [ ] `GET /health` y `GET /readyz` devuelven estado esperado.
- [ ] `POST /api/v1/invoices/emit` emite factura sin romper contrato.
- [ ] `GET /api/v1/invoices/{invoice_id}` retorna factura existente.
- [ ] `POST /api/v1/ecf/generate` genera XML/ECF esperado.

## 3. Operaciones críticas de negocio
- [ ] Flujo DGII recepción/envío (`/api/v1/ecf`, `/api/v1/status/{track_id}`) conserva respuestas.
- [ ] Flujos certificados (`/api/v1/internal/*`) mantienen intake/progreso/validación.
- [ ] Flujos billing/plan tenant en admin siguen operativos.

## 4. Persistencia de datos
- [ ] Crear/consultar factura persiste en BD.
- [ ] Crear token API cliente persiste y puede revocarse.
- [ ] Eventos de operación (`/api/v1/{operation_id}/events`) permanecen trazables.

## 5. Validaciones importantes
- [ ] Payload inválido de emisión devuelve 4xx (no 500).
- [ ] Endpoint protegido sin auth devuelve 401/403.
- [ ] Validaciones de formato fiscal (NCF/eNCF) conservan comportamiento.
