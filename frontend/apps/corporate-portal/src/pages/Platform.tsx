export function PlatformPage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <header className="max-w-3xl space-y-4">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Plataforma</p>
        <h1 className="text-4xl font-semibold text-ink">Arquitectura operativa para admin, clientes y socios.</h1>
        <p className="text-lg text-slate-600">
          GetUpSoft organiza la operacion sobre portales separados, control de permisos, evidencia funcional y una base preparada para integraciones contables y fiscales.
        </p>
      </header>
      <div className="mt-10 grid gap-6 md:grid-cols-3">
        <article className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6">
          <h2 className="text-xl font-semibold text-ink">Admin</h2>
          <p className="mt-3 text-sm text-slate-600">Gobierno multi-tenant, planes, auditoria, proveedores IA y configuracion global.</p>
        </article>
        <article className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6">
          <h2 className="text-xl font-semibold text-ink">Clientes</h2>
          <p className="mt-3 text-sm text-slate-600">Portal de emision, consulta, certificados, planes y asistente acotado por tenant.</p>
        </article>
        <article className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6">
          <h2 className="text-xl font-semibold text-ink">Socios</h2>
          <p className="mt-3 text-sm text-slate-600">Canal de revendedores con cartera asignada, emision demo y trazabilidad de cuenta.</p>
        </article>
      </div>
    </div>
  );
}
