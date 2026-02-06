# Seguridad del Proveedor DGII e-CF

Este documento establece las políticas mínimas de seguridad operativa para la plataforma DGII e-CF.

## 1. Bitácoras y trazabilidad

- Registrar cada solicitud realizada a la DGII con `request_id`, `track_id`, ambiente (`ENV`) y `rnc`.
- Mantener logs estructurados en formato JSON usando un backend central (ELK/CloudWatch).
- Configurar retención de logs mínima de 90 días en ambientes productivos.
- Enmascarar credenciales, tokens y contraseñas antes de persistir cualquier mensaje.

## 2. Respaldo y recuperación

- Base de datos: respaldos incrementales cada 15 minutos y respaldo completo diario.
- Archivos críticos (`.p12`, plantillas RI) almacenados en volumen cifrado (`AES-256`).
- Validar restauraciones trimestralmente en entornos aislados.
- Mantener script automatizado para restauración rápida (`infra/backup/restore.sh`).

## 3. Monitoreo y alertas

- Métricas de latencia, tasas de error y reintentos expuestas en `/metrics`.
- Alertas en: tasa de errores 5xx > 2% (5 minutos), demoras en reintentos DGII > 3 ciclos.
- Integración con canales de on-call (PagerDuty, Opsgenie) con escalamiento 24/7.

## 4. Gestión de incidentes

- Clasificar incidentes según impacto (P1 crítico hasta P4 informativo).
- Mantener runbooks específicos para: indisponibilidad DGII, certificados expirados, corrupción de datos RI.
- Reportar incidentes a la DGII cuando el impacto afecte SLA comprometido.
- Registrar post-mortems en menos de 72 horas con acciones preventivas.

## 5. Protección de datos

- Certificados y llaves almacenados fuera del repositorio (`/secrets`) con permisos `600`.
- Variables sensibles (`DGII_CERT_P12_PASSWORD`, tokens) gestionadas mediante Secret Manager o Vault.
- Cifrar datos en tránsito (TLS 1.2+) y en reposo (discos cifrados).
- Cumplir con la Ley 172-13 de Protección de Datos Personales.

## 6. Canales de soporte

- Mesa de ayuda primaria: soporte@getupsoft.com.do
- Canal urgente: +1 (809) XXX-XXXX (24/7)
- Escalamiento DGII: enlaces oficiales según ambiente (`PRECERT`, `CERT`, `PROD`).

## 7. Buenas prácticas adicionales

- Evaluaciones de seguridad semestrales (OWASP ASVS, análisis SAST/DAST).
- Revisiones del pipeline CI/CD para verificar firmas e integridad de artefactos.
- Política de rotación de contraseñas cada 90 días y MFA obligatorio para personal de operaciones.
