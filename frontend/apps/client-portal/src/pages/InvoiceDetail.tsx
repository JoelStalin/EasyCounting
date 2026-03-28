import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { useInvoiceDetail, useSendInvoiceEmail } from "../api/invoices";
import { useAuthStore } from "../store/auth-store";
import { resolveApiBaseUrl } from "../api/client";

async function downloadWithAuth(path: string, filename: string, token: string | null) {
  const response = await fetch(`${resolveApiBaseUrl()}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("No se pudo descargar el archivo");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function InvoiceDetailPage() {
  const { id } = useParams();
  const invoiceQuery = useInvoiceDetail(id);
  const invoice = invoiceQuery.data;
  const token = useAuthStore((state) => state.accessToken);
  const sendEmail = useSendInvoiceEmail();
  const [recipient, setRecipient] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  const formattedTotal = useMemo(() => {
    if (!invoice) return "RD$0.00";
    return Number(invoice.total).toLocaleString("es-DO", { style: "currency", currency: "DOP" });
  }, [invoice]);

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Detalle de comprobante #{id}</h1>
        <p className="text-sm text-slate-300">Visualiza XML, PDF DGII y envía la factura al cliente.</p>
      </header>

      {invoiceQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">No se pudo cargar el comprobante.</div>
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
            Monto: <span className="font-semibold text-primary">{formattedTotal}</span>
          </span>
        </div>

        <div className="flex gap-2 text-sm">
          <button
            type="button"
            className="rounded-md border border-slate-700 px-4 py-2 text-slate-200 hover:border-primary hover:text-primary"
            onClick={() => void downloadWithAuth(`/api/v1/cliente/invoices/${invoice?.id}/xml`, `${invoice?.encf ?? "factura"}.json`, token)}
            disabled={!invoice}
          >
            Descargar XML
          </button>
          <button
            type="button"
            className="rounded-md border border-slate-700 px-4 py-2 text-slate-200 hover:border-primary hover:text-primary"
            onClick={() => void downloadWithAuth(`/api/v1/cliente/invoices/${invoice?.id}/pdf`, `${invoice?.encf ?? "factura"}.pdf`, token)}
            disabled={!invoice || !invoice.ri_pdf_path}
          >
            Descargar PDF DGII
          </button>
        </div>

        <div className="grid grid-cols-1 gap-2 md:grid-cols-[1fr_auto]">
          <input
            value={recipient}
            onChange={(event) => setRecipient(event.target.value)}
            className="rounded-md border border-input bg-slate-950 px-3 py-2 text-sm"
            placeholder="correo@cliente.com"
            type="email"
          />
          <button
            type="button"
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
            disabled={!invoice || sendEmail.isPending || recipient.trim().length < 5}
            onClick={async () => {
              if (!invoice) return;
              try {
                const result = await sendEmail.mutateAsync({ invoiceId: invoice.id, recipient: recipient.trim() });
                setNotice(result.message);
              } catch {
                setNotice("No se pudo enviar la factura por correo.");
              }
            }}
          >
            {sendEmail.isPending ? "Enviando..." : "Enviar factura"}
          </button>
        </div>

        {notice ? <p className="text-xs text-emerald-300">{notice}</p> : null}

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
