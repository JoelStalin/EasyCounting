import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { RequirePermission } from "../auth/guards";
import { Spinner } from "../components/Spinner";
export function CertificatesPage() {
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);
    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setTimeout(() => {
            setLoading(false);
            setMessage("Certificado cargado y validado (simulado).");
        }, 800);
    };
    return (_jsx(RequirePermission, { anyOf: ["TENANT_CERT_UPLOAD"], children: _jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Certificados digitales" }), _jsx("p", { className: "text-sm text-slate-300", children: "Sube archivos .p12 y valida vigencia, issuer y subject." })] }), _jsxs("form", { onSubmit: handleSubmit, className: "space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-6", children: [_jsxs("label", { className: "block space-y-2 text-sm text-slate-300", children: ["Seleccionar archivo", _jsx("input", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", type: "file", accept: ".p12", required: true })] }), _jsxs("label", { className: "block space-y-2 text-sm text-slate-300", children: ["Contrase\u00F1a", _jsx("input", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", type: "password", required: true })] }), _jsx("div", { className: "flex justify-end", children: _jsx("button", { className: "flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground", type: "submit", disabled: loading, children: loading ? _jsx(Spinner, { label: "Validando" }) : "Subir" }) })] }), message ? _jsx("p", { className: "text-sm text-emerald-300", children: message }) : null] }) }));
}
