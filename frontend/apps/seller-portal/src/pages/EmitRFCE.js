import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { RequirePermission } from "../auth/guards";
import { Spinner } from "../components/Spinner";
export function EmitRFCEPage() {
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);
    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setTimeout(() => {
            setLoading(false);
            setMessage("RFCE transmitido correctamente (simulado).");
        }, 800);
    };
    return (_jsx(RequirePermission, { anyOf: ["TENANT_RFCE_SUBMIT"], children: _jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Emitir RFCE" }), _jsx("p", { className: "text-sm text-slate-300", children: "Env\u00EDa res\u00FAmenes para comprobantes menores a RD$250,000." })] }), _jsxs("form", { onSubmit: handleSubmit, className: "space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-6", children: [_jsxs("label", { className: "block space-y-2 text-sm text-slate-300", children: ["Resumen XML", _jsx("textarea", { className: "h-40 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-xs", required: true })] }), _jsx("div", { className: "flex justify-end", children: _jsx("button", { className: "flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground", type: "submit", disabled: loading, children: loading ? _jsx(Spinner, { label: "Enviando" }) : "Enviar" }) })] }), message ? _jsx("p", { className: "text-sm text-emerald-300", children: message }) : null] }) }));
}
