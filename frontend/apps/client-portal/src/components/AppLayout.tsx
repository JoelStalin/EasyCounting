import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/use-auth";
import { TourController } from "../tours/TourController";

const NAV = [
  { to: "/catalog", label: "Catalogo demo", permissions: [] },
  { to: "/checkout", label: "Cotizacion demo", permissions: [] },
  { to: "/dashboard", label: "Dashboard", permissions: ["TENANT_INVOICE_READ"] },
  { to: "/invoices", label: "Comprobantes", permissions: ["TENANT_INVOICE_READ"] },
  { to: "/plans", label: "Planes", permissions: ["TENANT_PLAN_VIEW", "TENANT_PLAN_UPGRADE"] },
  { to: "/assistant", label: "Asistente", permissions: ["TENANT_CHAT_ASSIST"] },
  { to: "/emit/ecf", label: "Emitir e-CF", permissions: ["TENANT_INVOICE_EMIT"] },
  { to: "/recurring-invoices", label: "Recurrentes", permissions: ["TENANT_RECURRING_INVOICE_MANAGE"] },
  { to: "/emit/rfce", label: "Emitir RFCE", permissions: ["TENANT_RFCE_SUBMIT"] },
  { to: "/approvals", label: "Aprobaciones", permissions: ["TENANT_APPROVAL_SEND"] },
  { to: "/certificates", label: "Certificados", permissions: ["TENANT_CERT_UPLOAD"] },
  { to: "/integrations/odoo", label: "API Odoo", permissions: ["TENANT_API_TOKEN_MANAGE"] },
  { to: "/profile", label: "Perfil", permissions: [] },
];

export function AppLayout() {
  const { logout, user, permissions } = useAuth();

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <aside className="hidden w-64 border-r border-slate-900 bg-slate-950/80 p-6 md:block">
        <div className="mb-8 space-y-1">
          <h2 className="text-xl font-semibold text-white">getupsoft Cliente</h2>
          <p className="text-xs text-slate-400">Gestion de comprobantes y flujos DGII.</p>
        </div>
        <nav className="space-y-2 text-sm" data-tour="portal-nav">
          {NAV.filter((item) => item.permissions.length === 0 || item.permissions.some((perm) => permissions.includes(perm))).map(
            (item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `block rounded-md px-3 py-2 transition ${isActive ? "bg-primary/20 text-primary" : "text-slate-300 hover:bg-slate-900"}`
                }
              >
                {item.label}
              </NavLink>
            ),
          )}
        </nav>
      </aside>
      <main className="flex-1">
        <header className="flex items-center justify-between border-b border-slate-900 bg-slate-950/60 px-6 py-4">
          <div data-tour="session-user">
            <p className="text-xs uppercase tracking-wide text-slate-400">Sesion</p>
            <p className="text-sm font-medium text-slate-200">{user?.email ?? "sin sesion"}</p>
          </div>
          <div className="flex items-center gap-3">
            <TourController />
            <button
              onClick={logout}
              className="rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-primary hover:text-primary"
            >
              Salir
            </button>
          </div>
        </header>
        <div className="px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
