# DGII Repeatable Browser Baseline

## Objetivo

Fijar una base repetible para la postulación DGII:

- mismo perfil fuente real de Chrome
- clon seguro del perfil vivo
- misma secuencia de pruebas
- misma clasificación de errores
- misma bitácora de salida

## Fuente de verdad

- Manifiesto reutilizable: `docs/certificados/autoasistido/dgii_postulacion_test_manifest.json`
- Último estado conocido: `docs/certificados/autoasistido/latest_known_state.json`
- Notas por corrida: `docs/certificados/autoasistido/run_notes/`

## Baseline del navegador

- Perfil fuente: `Default / JOEL STALIN`
- Estrategia: clonar el perfil a un `userDataDir` exclusivo para DGII
- Navegador: Chromium estable
- Política: `strict_normal_browser`
- Sin stealth
- Sin bypass de CSP
- Sin ignorar errores TLS
- Sin user agent artificial salvo que una prueba lo exija explícitamente

## Cadena auth

1. `session_reuse`
2. `portal_credentials`
3. `manual_seed`

## Regla de interpretación

- Warnings `Feature-Policy/Permissions-Policy` son `warning_non_blocking` salvo evidencia funcional.
- `Autenticación Fallida` en el portal se clasifica como `portal_credentials_invalid`.
