import { NavLink, Outlet } from "react-router-dom";

const NAV = [
  { to: "/", label: "Inicio" },
  { to: "/productos", label: "Productos" },
  { to: "/plataforma", label: "Plataforma" },
  { to: "/contacto", label: "Contacto" },
];

export function SiteLayout() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-sand/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-slate-500">GetUpSoft</p>
            <p className="text-lg font-semibold text-ink">Plataforma fiscal y operativa</p>
          </div>
          <nav className="hidden gap-6 text-sm font-medium text-slate-700 md:flex">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? "text-accent" : "hover:text-accent")}>
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <a className="rounded-full border border-slate-300 px-4 py-2 text-sm hover:border-accent hover:text-accent" href="https://admin.getupsoft.com.do/login">
              Admin
            </a>
            <a className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-accent" href="https://cliente.getupsoft.com.do/login">
              Ingresar
            </a>
          </div>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="border-t border-slate-200/80 bg-white/70">
        <div className="mx-auto grid max-w-7xl gap-6 px-6 py-10 md:grid-cols-3">
          <div>
            <p className="text-sm font-semibold text-ink">GetUpSoft</p>
            <p className="mt-2 text-sm text-slate-600">
              Software tax-tech y operaciones contables para empresas, partners y equipos administrativos.
            </p>
          </div>
          <div>
            <p className="text-sm font-semibold text-ink">Accesos</p>
            <ul className="mt-2 space-y-2 text-sm text-slate-600">
              <li><a href="https://admin.getupsoft.com.do/login">Admin</a></li>
              <li><a href="https://cliente.getupsoft.com.do/login">Clientes</a></li>
              <li><a href="https://socios.getupsoft.com.do/login">Socios</a></li>
            </ul>
          </div>
          <div>
            <p className="text-sm font-semibold text-ink">Producto destacado</p>
            <p className="mt-2 text-sm text-slate-600">
              Accounting Management: gestion contable, cumplimiento fiscal, reportes DGII y operacion multiempresa.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
