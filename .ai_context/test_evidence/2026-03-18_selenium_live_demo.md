# Selenium Live Demo - 2026-03-18

## Command

```powershell
powershell -ExecutionPolicy Bypass -File scripts\automation\run_selenium_live.ps1 -Browser chrome -SlowMoMs 1200 -KeepOpenMs 3000
```

## Result

- status: passed
- summary: `2 passed in 54.94s`

## Generated artifacts

- report:
  - `e2e/artifacts/live_20260318_154623/report.html`
- screenshots:
  - `e2e/artifacts/live_20260318_154623/*.png`

## Visual flow covered

- admin portal:
  - redirect to login
  - login
  - company list
  - create company modal
  - company detail
- client portal:
  - redirect to login
  - login
  - emit e-CF simulated
  - profile
  - logout

## Adaptations added for this project

- browser binary detection for installed Chrome/Edge in Windows
- headed execution with `HEADLESS=0`
- slow motion configurable with `SLOW_MO_MS`
- screenshots per step into `e2e/artifacts`
- self-contained HTML report opened automatically at the end
