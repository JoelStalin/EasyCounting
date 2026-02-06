# Frontend Monorepo (Admin & Client Portals)

Este directorio contiene los frontends en React + Vite + Tailwind para el ecosistema getupsoft.

## Estructura

- `apps/admin-portal`: Panel de plataforma para gestionar tenants, planes tarifarios, auditoría y usuarios RBAC.
- `apps/client-portal`: Portal para tenants con emisión de e-CF/RFCE, aprobaciones y administración de certificados.
- `packages/ui`: Biblioteca de componentes compartidos basada en Tailwind + shadcn/ui, exporta botones, inputs, tarjetas, badges y spinner accesibles.
- `packages/api-client`: Cliente Axios pre-configurado con soporte JWT, multi-tenant (`X-Tenant-ID`) y cabeceras de trazabilidad.

El workspace se orquesta con `pnpm`:

```bash
pnpm install
pnpm --filter @getupsoft/admin-portal dev
pnpm --filter @getupsoft/client-portal dev

# Compilación de ambas apps
pnpm build
```

## Estándares implementados

- **Autenticación** con Zustand + React Query, sincronizada con los endpoints FastAPI (`/auth/login`, `/auth/mfa/verify`, `/me`).
- **RBAC** en frontend mediante guardias `RequireAuth`, `RequirePermission` y `RequireScope`.
- **UI** basada en Tailwind y patrones inspirados en shadcn/ui para consistencia visual oscura.
- **Accesibilidad**: navegación por teclado, componentes con etiquetas y feedback claro en estados de error/permisos.
- **Seguridad**: almacenamiento de tokens en `sessionStorage` cifrado a nivel de transporte (TLS 1.3) + limpieza automática en errores 401.

## Próximos pasos

- Añadir Vitest + React Testing Library para pruebas unitarias de componentes y guardias.
- Integrar Storybook o Ladle para documentar componentes reutilizables.
- Conectar endpoints reales del backend (tenants, planes, comprobantes) una vez estén disponibles.
