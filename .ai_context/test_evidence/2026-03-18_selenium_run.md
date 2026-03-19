# Selenium Evidence - 2026-03-18

## Command

```powershell
$env:HEADLESS='1'; .\.venv\Scripts\python -m pytest e2e
```

## Result

- Status: passed
- Summary: `2 passed in 24.89s`

## Covered flows confirmed

- Admin portal:
  - protected route redirects to `/login`
  - login succeeds
  - tenant list loads
  - new tenant can be created from the modal
  - tenant detail route opens correctly
- Client portal:
  - protected route redirects to `/login`
  - login succeeds
  - `Emitir e-CF` form reaches the simulated success state
  - `Perfil` route renders authenticated user data
  - logout returns to `/login`
