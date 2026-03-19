import { BriefcaseBusiness, FileText, Wallet, Clock3 } from "lucide-react";
import { usePartnerDashboard, type PartnerTenantItem } from "../api/partner";
import { CardKPI } from "../components/CardKPI";

export function DashboardPage() {
  const dashboardQuery = usePartnerDashboard();
  const dashboard = dashboardQuery.data;

  const cards = [
    {
      title: "Clientes asignados",
      value: dashboard ? dashboard.tenantCount.toLocaleString("es-DO") : "…",
      subtitle: "Tenants visibles para esta cuenta",
      icon: <BriefcaseBusiness className="h-5 w-5 text-primary" aria-hidden />,
    },
    {
      title: "Comprobantes gestionados",
      value: dashboard ? dashboard.invoiceCount.toLocaleString("es-DO") : "…",
      subtitle: "e-CF dentro de la cartera actual",
      icon: <FileText className="h-5 w-5 text-primary" aria-hidden />,
    },
    {
      title: "Monto gestionado",
      value: dashboard
        ? Number(dashboard.totalAmount).toLocaleString("es-DO", {
            style: "currency",
            currency: "DOP",
            maximumFractionDigits: 2,
          })
        : "…",
      subtitle: "Sumatoria de comprobantes accesibles",
      icon: <Wallet className="h-5 w-5 text-primary" aria-hidden />,
    },
    {
      title: "Pendientes",
      value: dashboard ? dashboard.pendingCount.toLocaleString("es-DO") : "…",
      subtitle: "Documentos a seguimiento comercial/DGII",
      icon: <Clock3 className="h-5 w-5 text-primary" aria-hidden />,
    },
  ];

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Panel seller</h1>
        <p className="text-sm text-slate-300">
          Cartera asignada, volumen gestionado y control de emisiÃ³n por cliente.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <CardKPI key={card.title} {...card} />
        ))}
      </section>

      {dashboardQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo cargar el resumen del seller.
        </div>
      ) : null}

      <section className="space-y-3">
        <header className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Clientes destacados</h2>
          <p className="text-xs text-slate-400">{dashboard?.partner.accountName ?? "Sin cuenta comercial"}</p>
        </header>
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="min-w-full divide-y divide-slate-800 text-sm text-slate-300">
            <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-3 py-2 text-left">Cliente</th>
                <th className="px-3 py-2 text-left">Ambiente</th>
                <th className="px-3 py-2 text-left">Permisos</th>
                <th className="px-3 py-2 text-right">Comprobantes</th>
                <th className="px-3 py-2 text-right">Monto</th>
              </tr>
            </thead>
            <tbody>
              {dashboard?.tenants.map((tenant: PartnerTenantItem) => (
                <tr key={tenant.id} className="border-b border-slate-800/80 hover:bg-slate-900/40">
                  <td className="px-3 py-2 font-medium text-slate-100">{tenant.name}</td>
                  <td className="px-3 py-2">{tenant.env}</td>
                  <td className="px-3 py-2">{tenant.canEmit ? "Emite" : "Solo lectura"}</td>
                  <td className="px-3 py-2 text-right">{tenant.invoiceCount.toLocaleString("es-DO")}</td>
                  <td className="px-3 py-2 text-right">
                    {Number(tenant.totalAmount).toLocaleString("es-DO", {
                      style: "currency",
                      currency: "DOP",
                    })}
                  </td>
                </tr>
              ))}
              {dashboardQuery.isLoading ? (
                <tr>
                  <td className="px-3 py-6 text-center text-slate-500" colSpan={5}>
                    Cargando resumen…
                  </td>
                </tr>
              ) : null}
              {dashboard && dashboard.tenants.length === 0 ? (
                <tr>
                  <td className="px-3 py-6 text-center text-slate-500" colSpan={5}>
                    Esta cuenta seller todavÃ­a no tiene clientes asignados.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
