import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { useAuth } from "../auth/use-auth";
import { RequirePermission } from "../auth/guards";
import { Spinner } from "../components/Spinner";
export function EmitECFPage() {
    const { hasPermission } = useAuth();
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);
    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!hasPermission("TENANT_INVOICE_EMIT")) {
            setMessage("No tienes permisos para emitir e-CF.");
            return;
        }
        setLoading(true);
        setTimeout(() => {
            setLoading(false);
            setMessage("e-CF enviado a DGII (simulado).");
        }, 800);
    };
    return (_jsx(RequirePermission, { anyOf: ["TENANT_INVOICE_EMIT"], children: _jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Emitir e-CF" }), _jsx("p", { className: "text-sm text-slate-300", children: "Firma digitalmente el XML y env\u00EDalo a DGII con trazabilidad completa." })] }), _jsxs("form", { onSubmit: handleSubmit, className: "space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-6", children: [_jsxs("label", { className: "block space-y-2 text-sm text-slate-300", children: ["XML firmado (base64)", _jsx("textarea", { className: "h-40 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-xs", required: true })] }), _jsx("div", { className: "flex justify-end", children: _jsx("button", { className: "flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground", type: "submit", disabled: loading, children: loading ? _jsx(Spinner, { label: "Enviando" }) : "Enviar" }) })] }), message ? _jsx("p", { className: "text-sm text-emerald-300", children: message }) : null] }) }));
}
