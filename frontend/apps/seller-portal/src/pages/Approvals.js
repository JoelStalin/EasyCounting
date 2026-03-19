import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { RequirePermission } from "../auth/guards";
import { Spinner } from "../components/Spinner";
export function ApprovalsPage() {
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);
    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setTimeout(() => {
            setLoading(false);
            setMessage("ARECF enviado correctamente (simulado).");
        }, 800);
    };
    return (_jsx(RequirePermission, { anyOf: ["TENANT_APPROVAL_SEND"], children: _jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Aprobaciones y acuses" }), _jsx("p", { className: "text-sm text-slate-300", children: "Gestiona ARECF y ACECF siguiendo los motivos autorizados por DGII." })] }), _jsxs("form", { onSubmit: handleSubmit, className: "space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-6", children: [_jsxs("div", { className: "grid gap-4 md:grid-cols-3", children: [_jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["ENCF", _jsx("input", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", required: true })] }), _jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["Tipo", _jsxs("select", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", children: [_jsx("option", { value: "ARECF", children: "ARECF" }), _jsx("option", { value: "ACECF", children: "ACECF" })] })] }), _jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["Estado", _jsxs("select", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", children: [_jsx("option", { value: "0", children: "Recibido" }), _jsx("option", { value: "1", children: "No recibido" })] })] })] }), _jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["Motivo / detalle", _jsx("textarea", { className: "h-24 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm" })] }), _jsx("div", { className: "flex justify-end", children: _jsx("button", { className: "flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground", type: "submit", disabled: loading, children: loading ? _jsx(Spinner, { label: "Enviando" }) : "Enviar" }) })] }), message ? _jsx("p", { className: "text-sm text-emerald-300", children: message }) : null] }) }));
}
