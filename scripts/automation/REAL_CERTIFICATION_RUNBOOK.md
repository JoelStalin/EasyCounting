# Real Certification Runbook

This runbook defines a safe and reproducible flow for real DGII certification tests.

## Guardrails

- do not use AWS root user for automation
- do not expose `80/443` publicly without reverse proxy, TLS, and allowlist
- rotate any credential already shared in chat or screenshots
- keep DGII production and certification credentials strictly separated

## Mandatory Preconditions

1. Rotate AWS root password and enable MFA.
2. Create a dedicated IAM user/role for Route53 with least privilege.
3. Rotate DGII credentials and store them outside the repository.
4. Use a real signing certificate for the registered representative.
5. Define the real HostedZoneId for `getupsoft.com`.

## Minimal Route53 IAM Scope

Required actions:

- `route53:ListHostedZonesByName`
- `route53:ListResourceRecordSets`
- `route53:ChangeResourceRecordSets`
- `route53:GetChange`

Resource scope:

- exact hosted zone for `getupsoft.com`

## Secure WSL Start

```powershell
.\scripts\automation\start_wsl_local_service.ps1
```

Expected local endpoints:

- `http://127.0.0.1:28080` Nginx local test endpoint
- `http://127.0.0.1:18081` Admin SPA
- `http://127.0.0.1:18082` Client SPA
- `http://127.0.0.1:18083` Apex redirect

## DGII Signature Requirements Applied

- Postulacion XML must be signed by the registered representative/admin user.
- If certificate identity does not match that representative, DGII returns `Error XML. Firma Invalida.`.
- Certificate type must be `Persona Fisica para Procedimientos Tributarios` and align with Resolucion 035-2020, Art. 17.
- `VersionSoftware` must be numeric (`double`), for example `1.0`.

Official references:

- https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Documentacin%20sobre%20eCF/Instructivos%20sobre%20Facturaci%C3%B3n%20Electr%C3%B3nica/Firmado%20de%20e-CF.pdf
- https://ayuda.dgii.gov.do/conversations/facturacin-electrnica/ca5241-por-cules-razones-durante-el-proceso-de-certificacin-para-ser-emisor-electrnico-puede-generar-la-alerta-la-firma-utilizada-en-el-xml-del-formulario-de-postulacin-no-corresponde-con-el-representante-registrado-favor-verificar-y-volver-a-intentarlo/6824cc24cffeb5201cfd9039
- https://ayuda.dgii.gov.do/conversations/facturacin-electrnica/ca5270-en-cules-entidades-puedo-adquirir-el-certificado-digital-para-procesos-tributarios-exigido-en-facturacin-electrnica/68ac68a21c434d661376fe09
- https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Documents/Marco%20Legal/Resolucion%20035-2020.pdf

## Real Postulacion Sequence

1. Start backend and verify `/health` and `/readyz`.
2. Ensure real certificate is loaded/available.
3. Bootstrap DGII browser baseline from a cloned Chrome profile, never from the live profile.
4. Run Browser MCP postulacion flow with persistent `userDataDir`.
4. Generate postulacion XML.
5. Sign XML with real certificate.
6. Upload signed XML.
7. Persist artifacts and final DGII response.

## Repeatable DGII Browser Baseline

- Source profile: `Default / JOEL STALIN`
- Clone root: `DGII_POSTULACION_PROFILE_CLONE_ROOT`
- Working profile dir: `DGII_POSTULACION_PROFILE_DIR`
- Auth strategy order: `session_reuse,portal_credentials,manual_seed`
- Warnings `Feature-Policy/Permissions-Policy` are non-blocking unless correlated with a functional failure
- Persist after each run:
  - `docs/certificados/autoasistido/dgii_postulacion_test_manifest.json`
  - `docs/certificados/autoasistido/latest_known_state.json`
  - `docs/certificados/autoasistido/run_notes/*.md`

## Available Signing Tools

1. Internal API signing (tenant certificate):

```powershell
python scripts/automation/sign_postulacion_xml.py `
  --xml-path "C:\path\postulacion.xml" `
  --tenant-id 51
```

2. Local `.p12/.pfx` signing:

```powershell
python scripts/automation/sign_postulacion_xml.py `
  --xml-path "C:\path\postulacion.xml" `
  --p12-path "C:\path\certificado.p12" `
  --p12-password "********"
```

3. Official DGII tool (`App Firma Digital`) via automation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\automation\sign_with_dgii_app.ps1 `
  -XmlPath "C:\path\postulacion.xml" `
  -P12Path "C:\path\certificado.p12" `
  -P12Password "********"
```

4. Windows certificate store signing (token/store):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\automation\sign_with_windows_certstore.ps1 `
  -XmlPath "C:\path\postulacion.xml" `
  -StorePath "CurrentUser\My" `
  -Thumbprint "<REAL_CERT_THUMBPRINT>"
```

`scripts/automation/run_real_dgii_postulacion_ofv.py` and the Browser MCP postulacion flow now prioritize:

1. Internal API signing
2. Internal API retry after certificate register
3. Local `.p12/.pfx` signing
4. Windows store certificate signing
5. DGII App Firma Digital signing

The order can be overridden with `DGII_POSTULACION_SIGNING_ORDER`.

New environment variables:

- `DGII_SIGNING_CERT_THUMBPRINT`
- `DGII_SIGNING_CERT_SUBJECT`
- `DGII_SIGNING_CERT_STORE_PATH` (default `CurrentUser\My`)
- `DGII_APP_FIRMA_EXE_PATH`
- `DGII_POSTULACION_SIGNING_ORDER`

## Operational Evidence

Keep for each run:

- generated XML
- signed XML
- run-summary JSON
- final page screenshot and HTML
- DGII validation message

## Remaining Inputs Needed For Full Real Completion

- real representative certificate (`.p12/.pfx` or installed token cert)
- certificate password or token access flow
- rotated DGII credentials for certification environment
- dedicated IAM credentials (non-root)
