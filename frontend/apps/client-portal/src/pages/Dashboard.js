import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { FileText, ScanBarcode, ShieldCheck } from "lucide-react";
import { CardKPI } from "../components/CardKPI";
const KPIS = [
    {
        title: "Comprobantes emitidos",
        value: "1,245",
        subtitle: "Últimos 30 días",
        icon: _jsx(FileText, { className: "h-5 w-5 text-primary", "aria-hidden": true }),
    },
    {
        title: "RFCE enviados",
        value: "842",
        subtitle: "Procesados en modo resumen",
        icon: _jsx(ShieldCheck, { className: "h-5 w-5 text-primary", "aria-hidden": true }),
    },
    {
        title: "RI descargadas",
        value: "692",
        subtitle: "Con QR y hash de seguridad",
        icon: _jsx(ScanBarcode, { className: "h-5 w-5 text-primary", "aria-hidden": true }),
    },
];
export function DashboardPage() {
    return (_jsxs("div", { className: "space-y-8", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Resumen del tenant" }), _jsx("p", { className: "text-sm text-slate-300", children: "Seguimiento operativo de env\u00EDos DGII, planes tarifarios y controles de aprobaci\u00F3n." })] }), _jsx("section", { className: "grid gap-4 md:grid-cols-3", children: KPIS.map((kpi) => (_jsx(CardKPI, { ...kpi }, kpi.title))) }), _jsxs("section", { className: "space-y-3 text-sm text-slate-300", children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: "Pr\u00F3ximas acciones" }), _jsxs("ul", { className: "space-y-2", children: [_jsx("li", { children: "\u2022 Subir nuevo certificado .p12 antes de que expire el actual." }), _jsx("li", { children: "\u2022 Revisar aprobaciones comerciales pendientes (ACECF)." }), _jsx("li", { children: "\u2022 Ejecutar conciliaci\u00F3n con Odoo para facturas del mes." })] })] })] }));
}
