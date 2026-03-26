# Testing Strategy

## Ejecutado

- `python -m compileall app automation tests`
- `pytest tests/test_fiscal_operations.py automation/browser/tests/test_browser_feature_flags.py -q`
- `pytest tests/test_clients_contract.py -q`
- `python scripts/run_local_controlled_matrix.py`
- `pnpm --filter @getupsoft/admin-portal exec tsc --noEmit`
- `pnpm --filter @getupsoft/admin-portal build`

## Cobertura lograda

- flujo DGII durable
- Odoo transmit → pipeline DGII durable
- operaciones, eventos y SSE snapshot
- flags de browser automation
- cliente DGII contractual básico
- matriz local por tipos E31/E32/E33/E34/E41/E43/E44/E45/E46/E47
- monto `0.001` en corrida controlada

## No ejecutado por gate externo

- DGII `TEST/CERT` oficial
- Odoo JSON-2 contra servidor real
- browser automation contra portal real
