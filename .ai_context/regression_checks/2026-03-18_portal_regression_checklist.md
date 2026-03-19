# Regression Checklist - 2026-03-18

- Verify both compiled portal bundles are present and can be served as SPA static sites.
- Verify protected routes redirect to `/login` when no session exists.
- Verify login still persists session to the correct `sessionStorage` key.
- Verify admin company list still loads and allows creation through the modal.
- Verify company detail route still resolves tenant data after navigation.
- Verify tenant `Emitir e-CF` form still reaches the success state.
- Verify logout clears access to protected routes.
- Review `e2e/artifacts/` logs if startup or browser negotiation fails.
