import { usePartnerTenants, type PartnerTenantItem } from "../api/partner";

export function TenantsPage() {
  const tenantsQuery = usePartnerTenants();
  const tenants = tenantsQuery.data ?? [];

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Clientes asignados</h1>
        <p className="text-sm text-slate-300">
          El seller opera solo sobre la cartera que la plataforma le haya asignado.
        </p>
      </header>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="min-w-full divide-y divide-slate-800 text-sm text-slate-300">
          <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-3 py-2 text-left">Cliente</th>
              <th className="px-3 py-2 text-left">RNC</th>
              <th className="px-3 py-2 text-left">Ambiente</th>
              <th className="px-3 py-2 text-left">Estado</th>
              <th className="px-3 py-2 text-left">Permisos</th>
              <th className="px-3 py-2 text-right">Monto</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((tenant: PartnerTenantItem) => (
              <tr key={tenant.id} className="border-b border-slate-800/80 hover:bg-slate-900/40">
                <td className="px-3 py-2 font-medium text-slate-100">{tenant.name}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-400">{tenant.rnc}</td>
                <td className="px-3 py-2">{tenant.env}</td>
                <td className="px-3 py-2">{tenant.status}</td>
                <td className="px-3 py-2">
                  {tenant.canEmit ? "Puede emitir" : "Solo consulta"}
                  {tenant.canManage ? " · Puede administrar" : ""}
                </td>
                <td className="px-3 py-2 text-right">
                  {Number(tenant.totalAmount).toLocaleString("es-DO", {
                    style: "currency",
                    currency: "DOP",
                  })}
                </td>
              </tr>
            ))}
            {tenantsQuery.isLoading ? (
              <tr>
                <td className="px-3 py-6 text-center text-slate-500" colSpan={6}>
                  Cargando cartera del seller…
                </td>
              </tr>
            ) : null}
            {tenantsQuery.isError ? (
              <tr>
                <td className="px-3 py-6 text-center text-rose-200" colSpan={6}>
                  No se pudo consultar la asignaciÃ³n de clientes.
                </td>
              </tr>
            ) : null}
            {!tenantsQuery.isLoading && !tenantsQuery.isError && tenants.length === 0 ? (
              <tr>
                <td className="px-3 py-6 text-center text-slate-500" colSpan={6}>
                  No hay clientes asignados a esta cuenta.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
