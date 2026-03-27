# Runbook de Incidentes DGII

## 1. Certificado expirado
- Sintomas: firma falla con `Certificado fuera de vigencia`.
- Verificacion: revisar metadata cert y fecha `not_after`.
- Mitigacion inmediata: bloquear envio, activar certificado vigente.
- Correccion permanente: rotacion planificada + alerta previa.
- Evidencia: log de error, metadata cert, ticket.
- Comunicacion: notificar operaciones y responsable fiscal.

## 2. Password P12 incorrecta
- Sintomas: error al cargar PKCS#12.
- Verificacion: validar secreto en gestor y prueba local controlada.
- Mitigacion inmediata: corregir secreto en entorno.
- Correccion permanente: runbook de rotacion de secretos.
- Evidencia: evento de fallo de carga cert.
- Comunicacion: seguridad + plataforma.

## 3. Timeout DGII / En Proceso prolongado
- Sintomas: retries frecuentes o estado sin cierre.
- Verificacion: revisar DGIIAttempt, latencias y estado track.
- Mitigacion inmediata: mantener polling con backoff y sin duplicar envio.
- Correccion permanente: ajustar thresholds y alertas.
- Evidencia: historial intents + transiciones.
- Comunicacion: operaciones + negocio.

## 4. TrackId no persistido
- Sintomas: respuesta recibida pero sin trazabilidad DB.
- Verificacion: revisar transaccion `DGIIAttempt` y `FiscalOperation`.
- Mitigacion inmediata: replay controlado por idempotency key.
- Correccion permanente: test de regresion de persistencia.
- Evidencia: logs correlados.
- Comunicacion: backend owner.

## 5. Fuga de secretos en logs
- Sintomas: token/password visible en salida estructurada.
- Verificacion: revisar campos en logger sanitizado.
- Mitigacion inmediata: rotar secreto afectado y purgar logs sensibles.
- Correccion permanente: hardening en `_sanitize_context` + test.
- Evidencia: muestra de log redactada.
- Comunicacion: seguridad y cumplimiento.
