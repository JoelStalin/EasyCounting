# DEC-004 Real Signature Paths for DGII Postulacion

- Date: 2026-03-26
- Status: Accepted
- Scope: DGII real postulation XML signature automation

## Context

Real DGII postulation runs failed with signature rejections. Previous runs used test certificates (`CN=auto-sign.getupsoft.local`) and were not valid for taxpayer representative identity.

## Decision

Use a strict signature path hierarchy for real postulation:

1. Windows certificate store signer (`CurrentUser\My` or `LocalMachine\My`)
2. Official DGII App Firma Digital automation (`.p12/.pfx`)
3. Internal API tenant certificate fallback

Implemented in:

- `scripts/automation/run_real_dgii_postulacion_ofv.py`
- `scripts/automation/sign_with_windows_certstore.ps1`
- `scripts/automation/sign_with_dgii_app.ps1`

## Rationale

- Aligns with official requirement that postulation XML must be signed by registered representative identity.
- Supports both certificate-in-store (token/non-exportable workflows) and `.p12/.pfx` file workflows.
- Keeps browser automation separated from cryptographic key handling.
- Preserves reproducibility through explicit evidence artifacts.

## Consequences

- Automation now signs and uploads XML in one run when a certificate is available.
- If only non-matching certificate exists, DGII rejects with representative mismatch error; this is now explicit and auditable.
- Full real completion still depends on obtaining/installing the real representative certificate for RNC `22500706423`.

## Evidence

- `tests/artifacts/2026-03-26_03-06-33_dgii_real_postulacion_ofv/run-summary.json`
- `tests/artifacts/2026-03-26_03-06-33_dgii_real_postulacion_ofv/windows-store-sign-result.json`
- `tests/artifacts/2026-03-26_03-06-33_dgii_real_postulacion_ofv/after_signed_upload.json`
