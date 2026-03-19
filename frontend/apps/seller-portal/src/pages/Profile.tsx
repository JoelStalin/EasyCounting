import { usePartnerDashboard, usePartnerProfile } from "../api/partner";

export function ProfilePage() {
  const profileQuery = usePartnerProfile();
  const dashboardQuery = usePartnerDashboard();
  const profile = profileQuery.data;
  const dashboard = dashboardQuery.data;

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Perfil del socio</h1>
        <p className="text-sm text-slate-300">Resumen comercial y operativo de la cuenta seller.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Cuenta comercial</h2>
          <dl className="mt-4 space-y-3 text-sm text-slate-300">
            <div>
              <dt className="text-slate-500">Nombre</dt>
              <dd className="font-medium text-slate-100">{profile?.accountName ?? "Cargando…"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Slug</dt>
              <dd className="font-mono text-xs text-slate-300">{profile?.accountSlug ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Correo</dt>
              <dd className="font-medium text-slate-100">{profile?.userEmail ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Rol</dt>
              <dd className="font-medium text-slate-100">{profile?.role ?? "—"}</dd>
            </div>
          </dl>
        </article>

        <article className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Cobertura actual</h2>
          <dl className="mt-4 space-y-3 text-sm text-slate-300">
            <div>
              <dt className="text-slate-500">Clientes asignados</dt>
              <dd className="font-medium text-slate-100">{dashboard?.tenantCount ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Comprobantes visibles</dt>
              <dd className="font-medium text-slate-100">{dashboard?.invoiceCount ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Pendientes</dt>
              <dd className="font-medium text-slate-100">{dashboard?.pendingCount ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Monto gestionado</dt>
              <dd className="font-medium text-slate-100">
                {dashboard
                  ? Number(dashboard.totalAmount).toLocaleString("es-DO", {
                      style: "currency",
                      currency: "DOP",
                    })
                  : "—"}
              </dd>
            </div>
          </dl>
        </article>
      </section>

      {profileQuery.isError || dashboardQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo cargar el perfil completo del seller.
        </div>
      ) : null}
    </div>
  );
}
