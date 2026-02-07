import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { ShieldAlert } from "lucide-react";
export function ForbiddenState({ title = "Acceso denegado", description = "No cuentas con los permisos necesarios para ver esta sección.", }) {
    return (_jsxs("div", { className: "flex flex-col items-center justify-center gap-4 rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center", children: [_jsx(ShieldAlert, { className: "h-10 w-10 text-primary", "aria-hidden": true }), _jsxs("div", { className: "space-y-1", children: [_jsx("h2", { className: "text-xl font-semibold text-white", children: title }), _jsx("p", { className: "text-sm text-slate-300", children: description })] })] }));
}
