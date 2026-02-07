import { Link } from "react-router-dom";
import { useState } from "react";
import { RequirePermission } from "../auth/guards";
import { DataTable } from "../components/DataTable";
import { StatusBadge } from "../components/StatusBadge";
import { useUsageSummary } from "../api/usage";

const PAGE_SIZE = 20;

export function InvoicesPage() {
  const [page, setPage] = useState(1);
  const usageQuery = useUsageSummary({ page, size: PAGE_SIZE });
  const usage = usageQuery.data;
  const usageItems = usage?.items ?? [];

  return (
    <RequirePermission anyOf={["TENANT_INVOICE_READ", "TENANT_USAGE_VIEW"]}>
      <div className="space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-white">Comprobantes electronicos</h1>
            <p className="text-sm text-slate-300">Consulta estados DGII y consumo del mes en curso.</p>
          </div>
          <div className="flex gap-2">
            <Link className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground" to="/emit/ecf">
              Emitir e-CF
            </Link>
            <Link className="rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-200" to="/emit/rfce">
              Emitir RFCE
            </Link>
          </div>
        </header>

      <section className="grid gap-3 md:grid-cols-4">
        <StatCard label="Comprobantes usados" value={usage?.summary.total_used ?? 0} />
        <StatCard label="Incluidos" value={usage?.summary.included_documents ?? 0} />
        <StatCard label="Disponibles" value={usage?.summary.remaining_documents ?? 0} />
        <StatCard
          label="Cargos del mes"
          value={
            usage
              ? Number(usage.summary.total_amount).toLocaleString("es-DO", { style: "currency", currency: "DOP" })
              : "RD$0.00"
          }
        />
      </section>

      {usageQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo cargar el consumo del mes.
        </div>
      ) : null}

      <DataTable
        data={usageItems}
        emptyMessage={usageQuery.isLoading ? "Cargando comprobantes..." : "Sin comprobantes registrados"}
        columns={[
          {
            header: "Fecha",
            cell: (row) => (
              <span className="text-sm text-slate-300">
                {row.fecha_emision ? new Date(row.fecha_emision).toLocaleString() : new Date(row.fecha_uso).toLocaleString()}
              </span>
            ),
          },
          {
            header: "ENCF",
            cell: (row) =>
              row.invoice_id ? (
                <Link className="text-sm font-semibold text-primary" to={`/invoices/${row.invoice_id}`}>
                  {row.encf ?? "—"}
                </Link>
              ) : (
                <span className="text-sm text-slate-400">—</span>
              ),
          },
          {
            header: "Estado DGII",
            cell: (row) => (row.estado_dgii ? <StatusBadge status={row.estado_dgii} /> : <span className="text-sm text-slate-400">—</span>),
          },
          {
            header: "Total",
            cell: (row) => (
              <span className="text-sm text-slate-300">
                {row.total
                  ? Number(row.total).toLocaleString("es-DO", { style: "currency", currency: "DOP" })
                  : "—"}
              </span>
            ),
          },
          {
            header: "Cargo",
            cell: (row) => (
              <span className="text-sm text-slate-300">
                {Number(row.monto_cargado).toLocaleString("es-DO", { style: "currency", currency: "DOP" })}
              </span>
            ),
          },
        ]}
      />

        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>
            Pagina {usage?.page ?? page} · Total {usage?.total ?? 0}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded-md border border-slate-700 px-3 py-1.5 font-semibold text-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Anterior
            </button>
            <button
              type="button"
              onClick={() => setPage((p) => p + 1)}
              disabled={usageItems.length < PAGE_SIZE}
              className="rounded-md border border-slate-700 px-3 py-1.5 font-semibold text-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Siguiente
            </button>
          </div>
        </div>
      </div>
    </RequirePermission>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
}

function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-100">{value}</p>
    </div>
  );
}
