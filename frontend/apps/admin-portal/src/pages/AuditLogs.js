import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { JsonView } from "../components/JsonView";
import { useAuditLogs } from "../api/audit";
export function AuditLogsPage() {
    const logsQuery = useAuditLogs(50);
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Auditor\u00EDa" }), _jsx("p", { className: "text-sm text-slate-300", children: "Registros WORM con hash encadenado para cumplimiento DGII y PCI DSS." })] }), logsQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudieron cargar los logs de auditor\u00EDa." })) : null, _jsx(JsonView, { data: logsQuery.isLoading ? { loading: true } : logsQuery.data ?? [] })] }));
}
