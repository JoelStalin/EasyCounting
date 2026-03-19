# Risk Register - 2026-03-18

- `R1` Browser availability risk: Selenium run depends on Chrome or Edge being usable on the host.
- `R2` Build drift risk: stale `dist/` assets can make Selenium pass against older frontend code.
- `R3` Contract drift risk: if frontend API contracts change, the mock API must be updated in lockstep.
- `R4` Coverage gap: backend-integrated auth, DB persistence and DGII integrations are outside this local Selenium layer.
