# Checkpoint postulacion real DGII (2026-03-27 16:44)

## Estado alcanzado
- OFV autenticado correctamente (`/OFV/home.aspx`).
- Acceso a pantalla de solicitud de emisor electronico en OFV completado.
- Navegacion al Portal de Certificacion realizada.
- Punto de bloqueo actual: login en `https://ecf.dgii.gov.do/certecf/portalcertificacion/Login?...`.

## Evidencia grafica
- PDF consolidado: `docs/evidence/dgii_postulacion_visual_evidence_20260327_164434.pdf`
- Carpeta de corrida: `tests/artifacts/2026-03-27_16-44-34_dgii_real_postulacion_ofv/`

## Variables validadas
- `DGII_REAL_USERNAME=22500706423`
- `DGII_REAL_PASSWORD=Jm8296861202`
- `DGII_SIGNING_P12_PATH=C:\Users\yoeli\Documents\dgii_encf\app\dgii\certf\20260327-1854064-YNKAE7HKQ.p12`
- `DGII_SIGNING_P12_PASSWORD=Jm22500706423` (validada)

## Causa tecnica actual
El script usa las credenciales OFV para intentar login del Portal de Certificacion. Ese portal no esta aceptando esas credenciales de forma automatica (timeout de transicion post-submit).

## Siguiente paso para completarlo 100% automatico
1. Integrar credenciales propias del Portal de Certificacion (si son distintas a OFV):
   - `DGII_CERT_PORTAL_USERNAME`
   - `DGII_CERT_PORTAL_PASSWORD`
2. Reintentar flujo; al entrar a Postulacion:
   - generar XML
   - firmar con p12 validado
   - subir XML firmado
   - capturar respuesta final DGII
