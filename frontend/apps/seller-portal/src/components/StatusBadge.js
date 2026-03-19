import { jsx as _jsx } from "react/jsx-runtime";
const COLORS = {
    ACEPTADO: "bg-emerald-500/20 text-emerald-200",
    EN_PROCESO: "bg-amber-500/20 text-amber-200",
    RECHAZADO: "bg-red-500/20 text-red-200",
};
export function StatusBadge({ status }) {
    const color = COLORS[status] ?? "bg-slate-500/20 text-slate-200";
    return _jsx("span", { className: `rounded-full px-3 py-1 text-xs font-medium ${color}`, children: status });
}
