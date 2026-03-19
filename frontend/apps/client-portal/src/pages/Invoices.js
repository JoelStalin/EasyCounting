import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
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
    return (_jsx(RequirePermission, { anyOf: ["TENANT_INVOICE_READ", "TENANT_USAGE_VIEW"], children: _jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "flex items-center justify-between", children: [_jsxs("div", { children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Comprobantes electronicos" }), _jsx("p", { className: "text-sm text-slate-300", children: "Consulta estados DGII y consumo del mes en curso." })] }), _jsxs("div", { className: "flex gap-2", children: [_jsx(Link, { className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground", to: "/emit/ecf", children: "Emitir e-CF" }), _jsx(Link, { className: "rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-200", to: "/emit/rfce", children: "Emitir RFCE" })] })] }), _jsxs("section", { className: "grid gap-3 md:grid-cols-4", children: [_jsx(StatCard, { label: "Comprobantes usados", value: usage?.summary.total_used ?? 0 }), _jsx(StatCard, { label: "Incluidos", value: usage?.summary.included_documents ?? 0 }), _jsx(StatCard, { label: "Disponibles", value: usage?.summary.remaining_documents ?? 0 }), _jsx(StatCard, { label: "Cargos del mes", value: usage
                                ? Number(usage.summary.total_amount).toLocaleString("es-DO", { style: "currency", currency: "DOP" })
                                : "RD$0.00" })] }), usageQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo cargar el consumo del mes." })) : null, _jsx(DataTable, { data: usageItems, emptyMessage: usageQuery.isLoading ? "Cargando comprobantes..." : "Sin comprobantes registrados", columns: [
                        {
                            header: "Fecha",
                            cell: (row) => (_jsx("span", { className: "text-sm text-slate-300", children: row.fecha_emision ? new Date(row.fecha_emision).toLocaleString() : new Date(row.fecha_uso).toLocaleString() })),
                        },
                        {
                            header: "ENCF",
                            cell: (row) => row.invoice_id ? (_jsx(Link, { className: "text-sm font-semibold text-primary", to: `/invoices/${row.invoice_id}`, children: row.encf ?? "—" })) : (_jsx("span", { className: "text-sm text-slate-400", children: "\u2014" })),
                        },
                        {
                            header: "Estado DGII",
                            cell: (row) => (row.estado_dgii ? _jsx(StatusBadge, { status: row.estado_dgii }) : _jsx("span", { className: "text-sm text-slate-400", children: "\u2014" })),
                        },
                        {
                            header: "Total",
                            cell: (row) => (_jsx("span", { className: "text-sm text-slate-300", children: row.total
                                    ? Number(row.total).toLocaleString("es-DO", { style: "currency", currency: "DOP" })
                                    : "—" })),
                        },
                        {
                            header: "Cargo",
                            cell: (row) => (_jsx("span", { className: "text-sm text-slate-300", children: Number(row.monto_cargado).toLocaleString("es-DO", { style: "currency", currency: "DOP" }) })),
                        },
                    ] }), _jsxs("div", { className: "flex items-center justify-between text-xs text-slate-400", children: [_jsxs("span", { children: ["Pagina ", usage?.page ?? page, " \u00B7 Total ", usage?.total ?? 0] }), _jsxs("div", { className: "flex gap-2", children: [_jsx("button", { type: "button", onClick: () => setPage((p) => Math.max(1, p - 1)), disabled: page <= 1, className: "rounded-md border border-slate-700 px-3 py-1.5 font-semibold text-slate-200 disabled:cursor-not-allowed disabled:opacity-50", children: "Anterior" }), _jsx("button", { type: "button", onClick: () => setPage((p) => p + 1), disabled: usageItems.length < PAGE_SIZE, className: "rounded-md border border-slate-700 px-3 py-1.5 font-semibold text-slate-200 disabled:cursor-not-allowed disabled:opacity-50", children: "Siguiente" })] })] })] }) }));
}
function StatCard({ label, value }) {
    return (_jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-900/40 p-4", children: [_jsx("p", { className: "text-xs uppercase tracking-wide text-slate-400", children: label }), _jsx("p", { className: "mt-2 text-2xl font-semibold text-slate-100", children: value })] }));
}
