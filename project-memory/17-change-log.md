# Change Log

## 2026-03-25

- Mounted real DGII routers before legacy compatibility router.
- Added durable fiscal operation domain and persistence for events, attempts, evidence, and coverage.
- Added accounting hardening migration `20260325_0001_fiscal_ops_and_accounting_hardening.py`.
- Added controlled browser automation module with feature flags.
- Produced reproducible local evidence in `tests/artifacts/2026-03-25_23-50-25_controlled_local_matrix/`.

## 2026-03-26

- Implemented tenant certificate service and endpoints:
  - `GET /api/v1/cliente/certificates`
  - `POST /api/v1/cliente/certificates`
  - `POST /api/v1/cliente/certificates/sign-xml`
  - `POST /api/v1/internal/certificates/sign-xml`
  - `POST /api/v1/internal/certificates/register`
- Hardened internal origin validation for loopback/private bridge with `X-Internal-Secret`.
- Made certificate registration idempotent for existing tenant certificate.
- Updated DGII pipeline to prioritize tenant active certificate and safe environment fallback.
- Aligned RFCE, ANECF, ACECF, and ARECF routes with tenant/RNC certificate resolution.
- Re-ran backend tests:
  - `pytest tests/test_tenant_certificates.py tests/test_fiscal_operations.py -q`
  - Result: `8 passed`.
- Re-ran controlled local matrix with amount `0.001`:
  - `tests/artifacts/2026-03-26_02-13-10_controlled_local_matrix/`.
- Re-ran real DGII Selenium postulation and documented gates:
  - `tests/artifacts/2026-03-26_02-13-52_dgii_real_postulacion_ofv/`
  - Gate: `409 No existe un certificado utilizable para firmar`.
- Confirmed real DGII validation that `VersionSoftware` must be numeric (`double`) and normalized script behavior to `1.0`.
- Added `scripts/automation/sign_postulacion_xml.py` (`internal sign -> register -> sign -> local fallback`).
- Validated real run with automatic sign+upload:
  - `tests/artifacts/2026-03-26_02-33-33_dgii_real_postulacion_ofv/`
  - DGII response: `Error XML. Firma Invalida.`
- Expanded official investigation for valid postulation signature:
  - CA5241, CA5268, CA5270, `Firmado de e-CF`, Resolucion 035-2020.
- Added Windows certificate store signing tool:
  - `scripts/automation/sign_with_windows_certstore.ps1`
- Added Windows cert inventory tool:
  - `scripts/automation/list_windows_signing_certificates.ps1`
- Updated `scripts/automation/run_real_dgii_postulacion_ofv.py` to prioritize:
  1. Windows store signature
  2. DGII App Firma Digital
  3. Internal API and register fallback
- Rewrote `scripts/automation/REAL_CERTIFICATION_RUNBOOK.md` with updated signature requirements and tools.
- Executed real Selenium postulation using Windows store signer:
  - `tests/artifacts/2026-03-26_03-06-33_dgii_real_postulacion_ofv/`
  - Signature mode: `signed_with_windows_store`
  - Upload attempted: `true`
  - DGII response: `La firma utilizada en el XML del formulario de postulacion no corresponde con el representante registrado...`
  - Conclusion: automation path works; real representative certificate is still missing.
