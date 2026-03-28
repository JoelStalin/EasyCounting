import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { useTenantCertificates, useUploadTenantCertificate } from "../api/certificates";
import { RequirePermission } from "../auth/guards";
import { Spinner } from "../components/Spinner";
function formatDate(value) {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        return value;
    }
    return parsed.toLocaleString();
}
export function CertificatesPage() {
    const certificatesQuery = useTenantCertificates();
    const uploadCertificate = useUploadTenantCertificate();
    const [selectedFile, setSelectedFile] = useState(null);
    const [alias, setAlias] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);
    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!selectedFile) {
            setError("Selecciona un archivo .p12 o .pfx antes de continuar.");
            return;
        }
        setError(null);
        setMessage(null);
        try {
            const response = await uploadCertificate.mutateAsync({
                alias: alias.trim() || selectedFile.name.replace(/\.(p12|pfx)$/i, ""),
                password,
                certificate: selectedFile,
                activate: true,
            });
            setMessage(response.message);
            setPassword("");
            setSelectedFile(null);
            setAlias(response.alias);
        }
        catch (mutationError) {
            const fallback = "No se pudo cargar el certificado.";
            const detail = typeof mutationError === "object" &&
                mutationError !== null &&
                "response" in mutationError &&
                typeof mutationError.response?.data?.detail === "string"
                ? mutationError.response?.data?.detail
                : fallback;
            setError(detail ?? fallback);
        }
    };
    const items = certificatesQuery.data?.items ?? [];
    const activeSource = certificatesQuery.data?.activeSource ?? null;
    return (_jsx(RequirePermission, { anyOf: ["TENANT_CERT_UPLOAD"], children: _jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Certificados digitales" }), _jsx("p", { className: "text-sm text-slate-300", children: "Carga el .p12 del emisor y el sistema lo usara para firma automatica." })] }), _jsx("section", { className: "rounded-xl border border-slate-800 bg-slate-900/40 p-6", children: _jsxs("div", { className: "flex flex-wrap items-center justify-between gap-3", children: [_jsxs("div", { children: [_jsx("h2", { className: "text-sm font-semibold text-white", children: "Estado de firma automatica" }), _jsx("p", { className: "text-sm text-slate-300", children: activeSource === "tenant"
                                            ? "El tenant tiene un certificado activo listo para firmar."
                                            : activeSource === "env"
                                                ? "No hay certificado cargado por tenant; el backend esta usando el certificado global configurado."
                                                : "Aun no existe un certificado utilizable para firma automatica." })] }), certificatesQuery.isLoading ? _jsx(Spinner, { label: "Cargando certificados" }) : null] }) }), _jsxs("form", { onSubmit: handleSubmit, className: "space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-6", children: [_jsxs("label", { className: "block space-y-2 text-sm text-slate-300", children: ["Alias", _jsx("input", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", type: "text", value: alias, onChange: (event) => setAlias(event.target.value), placeholder: "Certificado DGII principal", maxLength: 100 })] }), _jsxs("label", { className: "block space-y-2 text-sm text-slate-300", children: ["Seleccionar archivo", _jsx("input", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", type: "file", accept: ".p12,.pfx", required: true, onChange: (event) => setSelectedFile(event.target.files?.[0] ?? null) })] }), _jsxs("label", { className: "block space-y-2 text-sm text-slate-300", children: ["Contrase\u00F1a", _jsx("input", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", type: "password", value: password, onChange: (event) => setPassword(event.target.value), required: true })] }), _jsx("div", { className: "flex justify-end", children: _jsx("button", { className: "flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:bg-slate-700", type: "submit", disabled: uploadCertificate.isPending, children: uploadCertificate.isPending ? _jsx(Spinner, { label: "Validando" }) : "Subir y activar" }) }), message ? _jsx("p", { className: "text-sm text-emerald-300", children: message }) : null, error ? _jsx("p", { className: "text-sm text-rose-300", children: error }) : null] }), _jsxs("section", { className: "rounded-xl border border-slate-800 bg-slate-900/40 p-6", children: [_jsxs("header", { className: "mb-4 space-y-1", children: [_jsx("h2", { className: "text-sm font-semibold text-white", children: "Certificados registrados" }), _jsx("p", { className: "text-sm text-slate-300", children: "El certificado activo es el que usara la firma automatica del portal DGII." })] }), certificatesQuery.isError ? (_jsx("p", { className: "text-sm text-rose-300", children: "No se pudo cargar el listado de certificados." })) : null, !certificatesQuery.isLoading && items.length === 0 ? (_jsx("p", { className: "text-sm text-slate-400", children: "Todavia no hay certificados cargados para este tenant." })) : null, items.length > 0 ? (_jsx("div", { className: "overflow-x-auto", children: _jsxs("table", { className: "min-w-full divide-y divide-slate-800 text-sm text-slate-200", children: [_jsx("thead", { children: _jsxs("tr", { className: "text-left text-xs uppercase tracking-wide text-slate-400", children: [_jsx("th", { className: "px-3 py-2", children: "Alias" }), _jsx("th", { className: "px-3 py-2", children: "Subject" }), _jsx("th", { className: "px-3 py-2", children: "Issuer" }), _jsx("th", { className: "px-3 py-2", children: "Vigencia" }), _jsx("th", { className: "px-3 py-2", children: "Estado" })] }) }), _jsx("tbody", { className: "divide-y divide-slate-900/60", children: items.map((item) => (_jsxs("tr", { children: [_jsx("td", { className: "px-3 py-3", children: item.alias }), _jsx("td", { className: "px-3 py-3 text-slate-300", children: item.subject }), _jsx("td", { className: "px-3 py-3 text-slate-300", children: item.issuer }), _jsxs("td", { className: "px-3 py-3 text-slate-300", children: [formatDate(item.notBefore), " ", _jsx("span", { className: "text-slate-500", children: "\u2192" }), " ", formatDate(item.notAfter)] }), _jsx("td", { className: "px-3 py-3", children: _jsx("span", { className: item.isActive
                                                            ? "rounded-full bg-emerald-950 px-2 py-1 text-xs font-semibold text-emerald-300"
                                                            : "rounded-full bg-slate-800 px-2 py-1 text-xs font-semibold text-slate-300", children: item.isActive ? "Activo" : "Registrado" }) })] }, item.id))) })] }) })) : null] })] }) }));
}
