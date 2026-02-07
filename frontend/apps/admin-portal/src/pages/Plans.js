import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link } from "react-router-dom";
import { usePlans } from "../api/plans";
import { DataTable } from "../components/DataTable";
export function PlansPage() {
    const plansQuery = usePlans();
    const rows = (plansQuery.data ?? []).map((plan) => ({
        id: plan.id,
        name: plan.name,
        documentos_incluidos: plan.documentos_incluidos,
        max_facturas_mes: plan.max_facturas_mes,
        max_facturas_por_receptor_mes: plan.max_facturas_por_receptor_mes,
        max_monto_por_factura: plan.max_monto_por_factura,
        precio_mensual: plan.precio_mensual,
        precio_por_documento: plan.precio_por_documento,
    }));
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "flex items-center justify-between", children: [_jsxs("div", { children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Planes tarifarios" }), _jsx("p", { className: "text-sm text-slate-300", children: "Define reglas de monetizaci\u00F3n para los tenants de getupsoft." })] }), _jsx(Link, { className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90", to: "/plans/new", children: "Nuevo plan" })] }), plansQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo cargar el listado de planes." })) : null, _jsx(DataTable, { data: rows, columns: [
                    { header: "Nombre", cell: (row) => _jsx("span", { className: "font-semibold text-slate-200", children: row.name }) },
                    { header: "Incluidos", cell: (row) => _jsx("span", { className: "text-sm text-slate-300", children: row.documentos_incluidos }) },
                    { header: "Máx/mes", cell: (row) => _jsx("span", { className: "text-sm text-slate-300", children: row.max_facturas_mes || "—" }) },
                    {
                        header: "Máx/cliente",
                        cell: (row) => _jsx("span", { className: "text-sm text-slate-300", children: row.max_facturas_por_receptor_mes || "—" }),
                    },
                    {
                        header: "Máx monto",
                        cell: (row) => (_jsx("span", { className: "text-sm text-slate-300", children: Number(row.max_monto_por_factura || 0).toLocaleString("es-DO", {
                                style: "currency",
                                currency: "DOP",
                            }) })),
                    },
                    { header: "Mensual", cell: (row) => _jsx("span", { className: "text-sm text-slate-300", children: row.precio_mensual }) },
                    { header: "Por doc.", cell: (row) => _jsx("span", { className: "text-sm text-slate-300", children: row.precio_por_documento }) },
                ], emptyMessage: plansQuery.isLoading ? "Cargando planes…" : plansQuery.isError ? "Error cargando planes" : "Sin planes" })] }));
}
