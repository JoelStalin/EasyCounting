import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { BriefcaseBusiness, FileText, Wallet, Clock3 } from "lucide-react";
import { usePartnerDashboard } from "../api/partner";
import { CardKPI } from "../components/CardKPI";
export function DashboardPage() {
    const dashboardQuery = usePartnerDashboard();
    const dashboard = dashboardQuery.data;
    const cards = [
        {
            title: "Clientes asignados",
            value: dashboard ? dashboard.tenantCount.toLocaleString("es-DO") : "…",
            subtitle: "Tenants visibles para esta cuenta",
            icon: _jsx(BriefcaseBusiness, { className: "h-5 w-5 text-primary", "aria-hidden": true }),
        },
        {
            title: "Comprobantes gestionados",
            value: dashboard ? dashboard.invoiceCount.toLocaleString("es-DO") : "…",
            subtitle: "e-CF dentro de la cartera actual",
            icon: _jsx(FileText, { className: "h-5 w-5 text-primary", "aria-hidden": true }),
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
            icon: _jsx(Wallet, { className: "h-5 w-5 text-primary", "aria-hidden": true }),
        },
        {
            title: "Pendientes",
            value: dashboard ? dashboard.pendingCount.toLocaleString("es-DO") : "…",
            subtitle: "Documentos a seguimiento comercial/DGII",
            icon: _jsx(Clock3, { className: "h-5 w-5 text-primary", "aria-hidden": true }),
        },
    ];
    return (_jsxs("div", { className: "space-y-8", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Panel seller" }), _jsx("p", { className: "text-sm text-slate-300", children: "Cartera asignada, volumen gestionado y control de emisi\u00C3\u00B3n por cliente." })] }), _jsx("section", { className: "grid gap-4 md:grid-cols-2 xl:grid-cols-4", children: cards.map((card) => (_jsx(CardKPI, { ...card }, card.title))) }), dashboardQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo cargar el resumen del seller." })) : null, _jsxs("section", { className: "space-y-3", children: [_jsxs("header", { className: "flex items-center justify-between", children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: "Clientes destacados" }), _jsx("p", { className: "text-xs text-slate-400", children: dashboard?.partner.accountName ?? "Sin cuenta comercial" })] }), _jsx("div", { className: "overflow-x-auto rounded-xl border border-slate-800", children: _jsxs("table", { className: "min-w-full divide-y divide-slate-800 text-sm text-slate-300", children: [_jsx("thead", { className: "bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400", children: _jsxs("tr", { children: [_jsx("th", { className: "px-3 py-2 text-left", children: "Cliente" }), _jsx("th", { className: "px-3 py-2 text-left", children: "Ambiente" }), _jsx("th", { className: "px-3 py-2 text-left", children: "Permisos" }), _jsx("th", { className: "px-3 py-2 text-right", children: "Comprobantes" }), _jsx("th", { className: "px-3 py-2 text-right", children: "Monto" })] }) }), _jsxs("tbody", { children: [dashboard?.tenants.map((tenant) => (_jsxs("tr", { className: "border-b border-slate-800/80 hover:bg-slate-900/40", children: [_jsx("td", { className: "px-3 py-2 font-medium text-slate-100", children: tenant.name }), _jsx("td", { className: "px-3 py-2", children: tenant.env }), _jsx("td", { className: "px-3 py-2", children: tenant.canEmit ? "Emite" : "Solo lectura" }), _jsx("td", { className: "px-3 py-2 text-right", children: tenant.invoiceCount.toLocaleString("es-DO") }), _jsx("td", { className: "px-3 py-2 text-right", children: Number(tenant.totalAmount).toLocaleString("es-DO", {
                                                        style: "currency",
                                                        currency: "DOP",
                                                    }) })] }, tenant.id))), dashboardQuery.isLoading ? (_jsx("tr", { children: _jsx("td", { className: "px-3 py-6 text-center text-slate-500", colSpan: 5, children: "Cargando resumen\u2026" }) })) : null, dashboard && dashboard.tenants.length === 0 ? (_jsx("tr", { children: _jsx("td", { className: "px-3 py-6 text-center text-slate-500", colSpan: 5, children: "Esta cuenta seller todav\u00C3\u00ADa no tiene clientes asignados." }) })) : null] })] }) })] })] }));
}
