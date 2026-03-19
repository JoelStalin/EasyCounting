import { Link } from "react-router-dom";

const metrics = [
  { label: "Portales", value: "3" },
  { label: "Cobertura", value: "Admin, cliente y socios" },
  { label: "Motor", value: "e-CF + DGII + Odoo" },
];

export function HomePage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-14">
      <section className="grid gap-10 lg:grid-cols-[1.15fr,0.85fr] lg:items-center">
        <div className="space-y-6">
          <span className="inline-flex rounded-full border border-accent/25 bg-accent/10 px-4 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-accent">
            Tax-tech y operaciones
          </span>
          <div className="space-y-4">
            <h1 className="max-w-3xl text-5xl font-semibold leading-tight text-ink">
              Gestion fiscal, contable y operativa desde una sola plataforma.
            </h1>
            <p className="max-w-2xl text-lg text-slate-600">
              GetUpSoft centraliza facturacion electronica, trazabilidad documental, control multiempresa y operacion contable con un enfoque listo para Republica Dominicana.
            </p>
          </div>
          <div className="flex flex-wrap gap-4">
            <a className="rounded-full bg-ink px-6 py-3 text-sm font-semibold text-white hover:bg-accent" href="https://cliente.getupsoft.com.do/login">
              Solicitar demo
            </a>
            <Link className="rounded-full border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-800 hover:border-accent hover:text-accent" to="/productos/accounting-management">
              Ver Accounting Management
            </Link>
          </div>
        </div>
        <div className="grid gap-4 rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-[0_30px_90px_rgba(15,23,42,0.08)]">
          {metrics.map((metric) => (
            <div key={metric.label} className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{metric.label}</p>
              <p className="mt-2 text-xl font-semibold text-ink">{metric.value}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-20 grid gap-6 md:grid-cols-3">
        <article className="rounded-[1.75rem] border border-slate-200 bg-white/85 p-6">
          <p className="text-sm font-semibold text-ink">Cumplimiento</p>
          <p className="mt-3 text-sm text-slate-600">Flujos preparados para e-CF, evidencia operativa y reportes orientados a DGII.</p>
        </article>
        <article className="rounded-[1.75rem] border border-slate-200 bg-white/85 p-6">
          <p className="text-sm font-semibold text-ink">Control</p>
          <p className="mt-3 text-sm text-slate-600">Portales diferenciados para plataforma, clientes y socios, con RBAC y segregacion por tenant.</p>
        </article>
        <article className="rounded-[1.75rem] border border-slate-200 bg-white/85 p-6">
          <p className="text-sm font-semibold text-ink">Integracion</p>
          <p className="mt-3 text-sm text-slate-600">Ruta de integracion con Odoo 19, reportes contables y operacion multiempresa.</p>
        </article>
      </section>
    </div>
  );
}
