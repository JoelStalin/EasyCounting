# Browser/Network audit DGII (2026-03-27)

## Objetivo
Extraer logs de consola navegador + endpoints observados del flujo real OFV para reproducir prueba y diagnosticar bloqueos.

## Corrida principal
- Artifact: `tests/artifacts/2026-03-27_17-12-44_dgii_network_console_audit/`
- Final URL: `https://dgii.gov.do/OFV/FacturaElectronica/FE_Facturador_Electronico.aspx`
- Endpoints detectados: 52
- Hosts principales:
  - `dgii.gov.do` (41)
  - `analytics.google.com` (3)
  - `www.googletagmanager.com` (2)

## Endpoints DGII relevantes observados
- `POST https://dgii.gov.do/OFV/login.aspx?ReturnUrl=%2fOFV%2fhome.aspx`
- `GET https://dgii.gov.do/OFV/home.aspx`
- `GET https://dgii.gov.do/OFV/FacturaElectronica/FE_Facturador_Electronico.aspx`
- `GET https://dgii.gov.do/Ofv/ScriptResource.axd?...`

## Hallazgos front relevantes (HTML)
Archivo: `03_solicitud_emisor.html`
- Botón `Acceder`: `ctl00_ContentPlaceHolder1_btnAcceso` (postback ASP.NET).
- Lógica JS detectada con `window.open(r.d.toString(), '_blank')` en flujo AJAX de scoring (no corresponde directo al botón de postulación).

## Console logs
- Solo warning DOM de autocomplete password (sin errores bloqueantes JS).

## Estado operativo actual
- Login OFV intermitente (mismo usuario/clave a veces entra, a veces vuelve al login).
- Desde pantalla "Solicitud para ser Emisor Electrónico", el click en `Acceder` no siempre abre la nueva ventana del portal en modo automatizado.
- Cuando se alcanza portal y se sube XML firmado, DGII responde historial con `Firma Inválida` (evidencia histórica de 2026-03-26).
