const features = [
  "Control de facturas, comprobantes y trazabilidad documental.",
  "Operacion contable y conciliacion con visibilidad multiempresa.",
  "Reportes orientados a DGII y seguimiento fiscal por tenant.",
  "Integracion con Odoo y portales diferenciados por perfil operativo.",
];

export function AccountingManagementPage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <header className="grid gap-8 lg:grid-cols-[1.15fr,0.85fr] lg:items-end">
        <div className="space-y-4">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Accounting Management</p>
          <h1 className="text-4xl font-semibold text-ink">Gestion contable y cumplimiento fiscal para operaciones reales.</h1>
          <p className="text-lg text-slate-600">
            Diseñado para empresas, firmas operativas y equipos administrativos que necesitan combinar control contable, emision y cumplimiento en un mismo flujo.
          </p>
        </div>
        <div className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6">
          <p className="text-sm font-semibold text-ink">Incluye</p>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {features.map((feature) => (
              <li key={feature}>{feature}</li>
            ))}
          </ul>
        </div>
      </header>

      <section className="mt-14 grid gap-6 md:grid-cols-2">
        <article className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6">
          <h2 className="text-xl font-semibold text-ink">Casos de uso</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Equipos de facturacion, backoffice financiero, firmas de outsourcing y grupos empresariales que requieren segregacion por tenant y trazabilidad clara.
          </p>
        </article>
        <article className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6">
          <h2 className="text-xl font-semibold text-ink">Resultado esperado</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Menos friccion operativa, mejor visibilidad de cumplimiento y una sola base para administracion, clientes y partners comerciales.
          </p>
        </article>
      </section>

      <section className="mt-14 rounded-[2rem] bg-ink px-8 py-10 text-white">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-300">Siguiente paso</p>
        <h2 className="mt-3 text-3xl font-semibold">Solicita una demo del servicio Accounting Management.</h2>
        <div className="mt-6 flex flex-wrap gap-4">
          <a className="rounded-full bg-white px-6 py-3 text-sm font-semibold text-ink" href="https://cliente.getupsoft.com.do/login">
            Ver portal cliente
          </a>
          <a className="rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white" href="https://admin.getupsoft.com.do/login">
            Ver portal admin
          </a>
        </div>
      </section>
    </div>
  );
}
