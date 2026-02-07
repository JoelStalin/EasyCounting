import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
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
            icon: _jsx(Building2, { className: "h-5 w-5 text-primary", "aria-hidden": true }),
        },
        {
            title: "Comprobantes del mes",
            value: kpis ? kpis.invoices_month.toLocaleString("es-DO") : "…",
            subtitle: "e-CF emitidos (todas las compañías)",
            icon: _jsx(Activity, { className: "h-5 w-5 text-primary", "aria-hidden": true }),
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
            icon: _jsx(Coins, { className: "h-5 w-5 text-primary", "aria-hidden": true }),
        },
    ];
    return (_jsxs("div", { className: "space-y-8", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Panel principal" }), _jsx("p", { className: "text-sm text-slate-300", children: "Monitorea la salud de los tenants, m\u00E9tricas de facturaci\u00F3n electr\u00F3nica y cumplimiento operativo." })] }), _jsx("section", { className: "grid gap-4 md:grid-cols-3", children: cards.map((kpi) => (_jsx(CardKPI, { ...kpi }, kpi.title))) }), kpisQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo cargar el resumen del dashboard." })) : null, _jsxs("section", { className: "space-y-3", children: [_jsxs("header", { className: "flex items-center justify-between", children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: "Comprobantes recientes" }), _jsxs("p", { className: "text-xs text-slate-400", children: ["Mostrando ", invoices?.items.length ?? 0, " de ", invoices?.total ?? 0] })] }), _jsx("div", { className: "overflow-x-auto rounded-xl border border-slate-800", children: _jsxs("table", { className: "min-w-full divide-y divide-slate-800 text-sm text-slate-300", children: [_jsx("thead", { className: "bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400", children: _jsxs("tr", { children: [_jsx("th", { className: "px-3 py-2 text-left", children: "Fecha" }), _jsx("th", { className: "px-3 py-2 text-left", children: "Compa\u00F1\u00EDa" }), _jsx("th", { className: "px-3 py-2 text-left", children: "ENCF" }), _jsx("th", { className: "px-3 py-2 text-left", children: "Tipo" }), _jsx("th", { className: "px-3 py-2 text-left", children: "Estado DGII" }), _jsx("th", { className: "px-3 py-2 text-right", children: "Total" })] }) }), _jsxs("tbody", { children: [invoices?.items.map((item) => (_jsxs("tr", { className: "border-b border-slate-800/80 hover:bg-slate-900/40", children: [_jsx("td", { className: "px-3 py-2", children: new Date(item.fecha_emision).toLocaleString() }), _jsx("td", { className: "px-3 py-2 font-medium text-slate-100", children: item.tenant_name }), _jsx("td", { className: "px-3 py-2 font-mono text-xs text-slate-400", children: item.encf }), _jsx("td", { className: "px-3 py-2", children: item.tipo_ecf }), _jsx("td", { className: "px-3 py-2", children: item.estado_dgii }), _jsx("td", { className: "px-3 py-2 text-right", children: Number(item.total).toLocaleString("es-DO", {
                                                        style: "currency",
                                                        currency: "DOP",
                                                    }) })] }, item.id))), invoicesQuery.isLoading ? (_jsx("tr", { children: _jsx("td", { className: "px-3 py-6 text-center text-sm text-slate-500", colSpan: 6, children: "Cargando comprobantes\u2026" }) })) : null, invoicesQuery.isError ? (_jsx("tr", { children: _jsx("td", { className: "px-3 py-6 text-center text-sm text-rose-200", colSpan: 6, children: "No se pudo cargar el listado de comprobantes." }) })) : null, invoices && invoices.items.length === 0 ? (_jsx("tr", { children: _jsx("td", { className: "px-3 py-6 text-center text-sm text-slate-500", colSpan: 6, children: "No hay comprobantes registrados a\u00FAn." }) })) : null] })] }) })] }), _jsxs("section", { className: "space-y-3", children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: "Pr\u00F3ximas acciones" }), _jsxs("ul", { className: "space-y-2 text-sm text-slate-300", children: [_jsx("li", { children: "\u2022 Validar ambiente de certificaci\u00F3n de nuevos clientes." }), _jsx("li", { children: "\u2022 Revisar alertas de planes con consumo at\u00EDpico." }), _jsx("li", { children: "\u2022 Confirmar renovaci\u00F3n de certificados digitales." })] })] })] }));
}
