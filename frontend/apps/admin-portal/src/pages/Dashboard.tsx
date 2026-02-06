import { Activity, Building2, Coins } from "lucide-react";
import { CardKPI } from "../components/CardKPI";
import { useAdminInvoices, useDashboardKpis } from "../api/dashboard";

export function DashboardPage() {
  const kpisQuery = useDashboardKpis();
  const invoicesQuery = useAdminInvoices({ page: 1, size: 10 });
  const kpis = kpisQuery.data;
  const invoices = invoicesQuery.data;

  const amountDue = kpis ? Number(kpis.amount_due_month ?? 0) : 0;

  const cards = [
    {
      title: "Compañías activas",
      value: kpis ? String(kpis.companies_active) : "…",
      subtitle: "Tenants con integración DGII operativa",
      icon: <Building2 className="h-5 w-5 text-primary" aria-hidden />,
    },
    {
      title: "Comprobantes del mes",
      value: kpis ? kpis.invoices_month.toLocaleString("es-DO") : "…",
      subtitle: "e-CF emitidos (todas las compañías)",
      icon: <Activity className="h-5 w-5 text-primary" aria-hidden />,
    },
    {
      title: "Monto a facturar (mes)",
      value: kpis
        ? amountDue.toLocaleString("es-DO", {
            style: "currency",
            currency: "DOP",
            maximumFractionDigits: 2,
          })
        : "…",
      subtitle: "Cargos por uso acumulados",
      icon: <Coins className="h-5 w-5 text-primary" aria-hidden />,
    },
  ];

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Panel principal</h1>
        <p className="text-sm text-slate-300">
          Monitorea la salud de los tenants, métricas de facturación electrónica y cumplimiento operativo.
        </p>
      </header>
      <section className="grid gap-4 md:grid-cols-3">
        {cards.map((kpi) => (
          <CardKPI key={kpi.title} {...kpi} />
        ))}
      </section>

      {kpisQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo cargar el resumen del dashboard.
        </div>
      ) : null}

      <section className="space-y-3">
        <header className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Comprobantes recientes</h2>
          <p className="text-xs text-slate-400">
            Mostrando {invoices?.items.length ?? 0} de {invoices?.total ?? 0}
          </p>
        </header>
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="min-w-full divide-y divide-slate-800 text-sm text-slate-300">
            <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-3 py-2 text-left">Fecha</th>
                <th className="px-3 py-2 text-left">Compañía</th>
                <th className="px-3 py-2 text-left">ENCF</th>
                <th className="px-3 py-2 text-left">Tipo</th>
                <th className="px-3 py-2 text-left">Estado DGII</th>
                <th className="px-3 py-2 text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              {invoices?.items.map((item) => (
                <tr key={item.id} className="border-b border-slate-800/80 hover:bg-slate-900/40">
                  <td className="px-3 py-2">{new Date(item.fecha_emision).toLocaleString()}</td>
                  <td className="px-3 py-2 font-medium text-slate-100">{item.tenant_name}</td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-400">{item.encf}</td>
                  <td className="px-3 py-2">{item.tipo_ecf}</td>
                  <td className="px-3 py-2">{item.estado_dgii}</td>
                  <td className="px-3 py-2 text-right">
                    {Number(item.total).toLocaleString("es-DO", {
                      style: "currency",
                      currency: "DOP",
                    })}
                  </td>
                </tr>
              ))}
              {invoicesQuery.isLoading ? (
                <tr>
                  <td className="px-3 py-6 text-center text-sm text-slate-500" colSpan={6}>
                    Cargando comprobantes…
                  </td>
                </tr>
              ) : null}
              {invoicesQuery.isError ? (
                <tr>
                  <td className="px-3 py-6 text-center text-sm text-rose-200" colSpan={6}>
                    No se pudo cargar el listado de comprobantes.
                  </td>
                </tr>
              ) : null}
              {invoices && invoices.items.length === 0 ? (
                <tr>
                  <td className="px-3 py-6 text-center text-sm text-slate-500" colSpan={6}>
                    No hay comprobantes registrados aún.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Próximas acciones</h2>
        <ul className="space-y-2 text-sm text-slate-300">
          <li>• Validar ambiente de certificación de nuevos clientes.</li>
          <li>• Revisar alertas de planes con consumo atípico.</li>
          <li>• Confirmar renovación de certificados digitales.</li>
        </ul>
      </section>
    </div>
  );
}
