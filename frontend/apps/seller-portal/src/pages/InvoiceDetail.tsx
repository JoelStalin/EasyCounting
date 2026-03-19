import { useParams } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { useInvoiceDetail } from "../api/invoices";

export function InvoiceDetailPage() {
  const { id } = useParams();
  const invoiceQuery = useInvoiceDetail(id);
  const invoice = invoiceQuery.data;

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Detalle de comprobante #{id}</h1>
        <p className="text-sm text-slate-300">Visualiza XML firmado, RI y bitacora de auditoria.</p>
      </header>

      {invoiceQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo cargar el comprobante.
        </div>
      ) : null}

      <section className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-300">
          <span>
            ENCF: <span className="font-mono text-slate-100">{invoice?.encf ?? "?"}</span>
          </span>
          {invoice?.estado_dgii ? <StatusBadge status={invoice.estado_dgii} /> : null}
          <span>
            Track ID: <span className="font-mono text-slate-100">{invoice?.track_id ?? "?"}</span>
          </span>
          <span>
            Monto:{" "}
            <span className="font-semibold text-primary">
              {invoice ? Number(invoice.total).toLocaleString("es-DO", { style: "currency", currency: "DOP" }) : "RD$0.00"}
            </span>
          </span>
        </div>
        <div className="flex gap-2 text-sm">
          <button
            type="button"
            className="rounded-md border border-slate-700 px-4 py-2 text-slate-200 hover:border-primary hover:text-primary"
            disabled
          >
            Descargar XML
          </button>
          <button
            type="button"
            className="rounded-md border border-slate-700 px-4 py-2 text-slate-200 hover:border-primary hover:text-primary"
            disabled
          >
            Descargar RI
          </button>
        </div>
        <div className="space-y-2 text-xs text-slate-300">
          <p>
            Hash auditoria: <span className="font-mono">{invoice?.xml_hash ?? "?"}</span>
          </p>
          <p>
            Estado contable: <span className="font-mono">{invoice?.contabilizado ? "Contabilizado" : "Pendiente"}</span>
          </p>
        </div>
      </section>
    </div>
  );
}
