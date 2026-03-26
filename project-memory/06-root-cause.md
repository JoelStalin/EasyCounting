# Root Cause

## Causa raíz principal

La plataforma no tenía un modelo de operación fiscal durable que coordinara DGII, contabilidad y observabilidad. Como resultado, el `TrackId`, los estados, los intentos, la evidencia y la futura sincronización con Odoo quedaban dispersos o incompletos.

## Causas secundarias

- Enrutamiento incorrecto: las rutas fake de compatibilidad DGII quedaban por delante de las reales.
- Precisión insuficiente en contabilidad y facturación: `Numeric(16,2)` impedía soportar `0.001` end-to-end.
- Acoplamiento débil con Odoo: no había bridge JSON-2 real ni mapping persistido por tenant.
- Observabilidad parcial: el stream SSE no respetaba la sesión efectiva del entorno de prueba.
- Migraciones incompletas respecto al metadata real.
