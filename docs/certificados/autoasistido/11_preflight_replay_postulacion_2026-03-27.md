# Preflight replay postulacion real (2026-03-27)

## Objetivo
Repetir prueba historica hasta `after_signed_upload` con trazabilidad y control de errores.

## Estado base confirmado
- Run historico que llego a upload: `tests/artifacts/2026-03-26_04-01-53_dgii_real_postulacion_ofv/`.
- Evidencia de upload: `after_signed_upload.json` (resultado: `Error XML. Firma Inválida`).

## Riesgos evaluados antes de correr
1. **Login OFV intermitente**: el submit devuelve a login sin mensaje visible.
2. **Popup Acceder**: puede no abrir portal en modo automatizado.
3. **Portal login separado**: puede requerir credenciales diferentes a OFV.
4. **Firma XML**: aunque suba, DGII puede rechazar por identidad de firmante.

## Mitigaciones aplicadas
- Timeout extendido y captura explícita de popup en `run_real_dgii_postulacion_ofv.py`.
- Flag Chrome `--disable-popup-blocking` en launcher debug.
- Capturas automáticas en cada etapa (`*.png/*.html/*.json`).

## Credenciales y firma validadas
- OFV user: `22500706423`
- OFV pass: `Jm8296861202`
- P12 path: `app/dgii/certf/20260327-1854064-YNKAE7HKQ.p12`
- P12 pass válida: `Jm22500706423`
