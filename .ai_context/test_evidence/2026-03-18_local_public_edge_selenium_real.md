# 2026-03-18 - Local public edge Selenium on real backend

## Preconditions validated

- `http://127.0.0.1:28080/healthz` -> `200`
- `http://127.0.0.1:18081/login` -> `200`
- `http://127.0.0.1:18082/login` -> `200`
- `http://127.0.0.1:18083/foo/bar?x=1` -> `301` to `https://admin.getupsoft.com.do/foo/bar?x=1`
- CORS preflight for `POST /auth/login` from both `http://127.0.0.1:18081` and `http://127.0.0.1:18082` -> `200`

## Selenium runs

### Chrome

Command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\automation\run_selenium_live.ps1 -Browser chrome -SlowMoMs 400 -KeepOpenMs 3000 -AdminBaseUrl http://127.0.0.1:18081 -ClientBaseUrl http://127.0.0.1:18082 -ApiBaseUrl http://127.0.0.1:28080
```

Result:

- `2 passed in 39.22s`
- Report: `e2e/artifacts/live_20260318_193353/report.html`

Covered visually:

- admin login
- company listing
- `Agentes IA`
- tenant creation
- company detail open
- client login
- simulated e-CF emit flow
- profile open
- logout

### Edge

Command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\automation\run_selenium_live.ps1 -Browser edge -SlowMoMs 400 -KeepOpenMs 3000 -AdminBaseUrl http://127.0.0.1:18081 -ClientBaseUrl http://127.0.0.1:18082 -ApiBaseUrl http://127.0.0.1:28080
```

Result:

- `2 passed in 40.88s`
- Report: `e2e/artifacts/live_20260318_193732/report.html`

## Notes

- These runs were executed against the real local backend, not the mock API harness.
- Edge exposed two useful test issues that were fixed before the final passing run:
  - modal-close race after tenant creation
  - test-data collision across browser reruns due reused RNC
