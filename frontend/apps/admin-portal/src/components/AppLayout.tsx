import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/use-auth";

const NAV = [
  { to: "/dashboard", label: "Dashboard", permissions: ["PLATFORM_TENANT_VIEW", "PLATFORM_PLAN_CRUD"] },
  { to: "/companies", label: "Compañías", permissions: ["PLATFORM_TENANT_VIEW"] },
  { to: "/plans", label: "Planes", permissions: ["PLATFORM_PLAN_CRUD"] },
  { to: "/ai-providers", label: "Agentes IA", permissions: ["PLATFORM_AI_PROVIDER_MANAGE"] },
  { to: "/audit-logs", label: "Auditoría", permissions: ["PLATFORM_AUDIT_VIEW"] },
  { to: "/users", label: "Usuarios", permissions: ["PLATFORM_USER_MANAGE"] },
];

export function AppLayout() {
  const { logout, user, permissions } = useAuth();

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <aside className="hidden w-64 border-r border-slate-900 bg-slate-950/80 p-6 lg:block">
        <div className="mb-8 space-y-1">
          <h2 className="text-xl font-semibold text-white">getupsoft Admin</h2>
          <p className="text-xs text-slate-400">Operación multi-tenant y cumplimiento DGII.</p>
        </div>
        <nav className="space-y-2 text-sm">
          {NAV.filter((item) => item.permissions.some((perm) => permissions.includes(perm))).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center rounded-md px-3 py-2 transition ${isActive ? "bg-primary/20 text-primary" : "text-slate-300 hover:bg-slate-900"}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1">
        <header className="flex items-center justify-between border-b border-slate-900 bg-slate-950/60 px-6 py-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Usuario autenticado</p>
            <p className="text-sm font-medium text-slate-200">{user?.email ?? "sesión no activa"}</p>
          </div>
          <button
            onClick={logout}
            className="rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-primary hover:text-primary"
          >
            Cerrar sesión
          </button>
        </header>
        <div className="px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
