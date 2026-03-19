import { useState } from "react";
import { usePartnerInvoices, usePartnerTenants, type PartnerInvoiceItem, type PartnerTenantItem } from "../api/partner";

export function InvoicesPage() {
  const [tenantId, setTenantId] = useState<number | null>(null);
  const tenantsQuery = usePartnerTenants();
  const invoicesQuery = usePartnerInvoices({ tenantId, page: 1, size: 25 });
  const invoices = invoicesQuery.data;

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Comprobantes de la cartera</h1>
        <p className="text-sm text-slate-300">
          Vista consolidada de documentos visibles para el reseller, operador o auditor.
        </p>
      </header>

      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <label className="space-y-2 text-sm text-slate-300">
          <span className="block text-xs uppercase tracking-wide text-slate-400">Filtrar por cliente</span>
          <select
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
            value={tenantId ?? ""}
            onChange={(event) => {
              const value = event.target.value;
              setTenantId(value ? Number(value) : null);
            }}
          >
            <option value="">Todos los clientes asignados</option>
            {(tenantsQuery.data ?? []).map((tenant: PartnerTenantItem) => (
              <option key={tenant.id} value={tenant.id}>
                {tenant.name}
              </option>
            ))}
          </select>
        </label>
      </section>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="min-w-full divide-y divide-slate-800 text-sm text-slate-300">
          <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-3 py-2 text-left">Fecha</th>
              <th className="px-3 py-2 text-left">Cliente</th>
              <th className="px-3 py-2 text-left">ENCF</th>
              <th className="px-3 py-2 text-left">Tipo</th>
              <th className="px-3 py-2 text-left">Estado</th>
              <th className="px-3 py-2 text-left">Track ID</th>
              <th className="px-3 py-2 text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {invoices?.items.map((item: PartnerInvoiceItem) => (
              <tr key={item.id} className="border-b border-slate-800/80 hover:bg-slate-900/40">
                <td className="px-3 py-2">{new Date(item.fechaEmision).toLocaleString("es-DO")}</td>
                <td className="px-3 py-2 font-medium text-slate-100">{item.tenantName}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-400">{item.encf}</td>
                <td className="px-3 py-2">{item.tipoEcf}</td>
                <td className="px-3 py-2">{item.estadoDgii}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-500">{item.trackId ?? "sin track"}</td>
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
                <td className="px-3 py-6 text-center text-slate-500" colSpan={7}>
                  Cargando comprobantes…
                </td>
              </tr>
            ) : null}
            {invoicesQuery.isError ? (
              <tr>
                <td className="px-3 py-6 text-center text-rose-200" colSpan={7}>
                  No se pudo cargar el listado de comprobantes del seller.
                </td>
              </tr>
            ) : null}
            {invoices && invoices.items.length === 0 ? (
              <tr>
                <td className="px-3 py-6 text-center text-slate-500" colSpan={7}>
                  No hay comprobantes disponibles para este filtro.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
