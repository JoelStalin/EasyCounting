# 07 - Estado Actual y Punto de Reanudacion (2026-03-27)

## Contexto confirmado
- Dominio operativo del repo: `getupsoft.com.do`.
- Exposicion web: Cloudflare Tunnel para servicios HTTP/HTTPS.
- Evidencia legal recibida: contrato Viafirma (`S9Z81774635165329R838.pdf`).
- Evidencia operativa adicional: timeline RA Viafirma con certificado generado y opcion de descarga (`08_viafirma_timeline_obtencion_p12_2026-03-27.md`).

## Lectura operativa del documento Viafirma
- El PDF corresponde al contrato de prestacion del certificado digital (RA/CA Viafirma).
- Este documento confirma avance de etapa humana/legal del proceso (aceptacion contractual y condiciones de uso).
- No contiene por si solo el `.p12/.pfx`; por tanto no cierra `CERTIFICATE_RECEIVED`.

## Punto exacto de reanudacion sugerido
- Estado funcional: `HUMAN_SUBMISSION_DONE` o `PSC_APPROVED` (segun confirmacion final de emision en RA).
- Siguiente estado objetivo: `CERTIFICATE_RECEIVED` por ingesta controlada (mail intake o carga segura manual).

## Estado del modulo de mail intake (retomar desde aqui)
- Integracion implementada:
  - servicio IMAP + parseo de adjuntos `.p12/.pfx`;
  - endpoint `POST /api/v1/internal/certificate-workflow/mail-intake/process`;
  - endpoint `GET /api/v1/internal/certificate-workflow/mail-intake/health`;
  - pruebas unitarias en verde.
- Punto pendiente para produccion:
  - activar credenciales reales Mailcow (`CERTIFICATE_WORKFLOW_MAIL_INTAKE_*`);
  - ejecutar health en vivo y primer ciclo de proceso.

## Checklist de continuidad inmediata
1. Confirmar que el asunto/cuerpo de correo de Viafirma incluya `case_id` con patron `PSC-YYYY-NNNNN`.
2. Habilitar mailbox `certificados@getupsoft.com.do` en Mailcow.
3. Configurar variables `CERTIFICATE_WORKFLOW_MAIL_INTAKE_*` en entorno real.
4. Validar conexion IMAP:
   - `GET /api/v1/internal/certificate-workflow/mail-intake/health`
5. Ejecutar disparo manual:
   - `POST /api/v1/internal/certificate-workflow/mail-intake/process?limit=25`
6. Verificar que se registren eventos:
   - `MAIL_INTAKE_EMAIL_RECEIVED`
   - `CERTIFICATE_RECEIVED`
   - `CERTIFICATE_VALIDATED` o `CERTIFICATE_VALIDATION_FAILED`
7. Si no viene password en el correo:
   - resolver evento `MAIL_INTAKE_PASSWORD_MISSING` y revalidar por canal seguro.

## Riesgos abiertos
- Si Viafirma no envia `case_id`, el correo no se puede vincular automaticamente al caso.
- Si password llega por canal separado, se requiere paso humano asistido.
- Si Cloudflare Tunnel se usa para correo, IMAP/SMTP/MX no funcionara correctamente.
