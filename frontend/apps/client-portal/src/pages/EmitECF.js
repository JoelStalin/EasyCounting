import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { useAuth } from "../auth/use-auth";
import { RequirePermission } from "../auth/guards";
import { Spinner } from "../components/Spinner";
import { useEmitInvoice } from "../api/invoices";
import { useFormTutor } from "../tutorial/hooks/useFormTutor";
import { TutorContextualIcon } from "../tutorial/components/TutorContextualIcon";
import { EmitEcfTutorConfig } from "../tutorial/config/emitEcfTutor";
export function EmitECFPage() {
    const { hasPermission } = useAuth();
    const emitMutation = useEmitInvoice();
    const [encf, setEncf] = useState("");
    const [tipoEcf, setTipoEcf] = useState("31");
    const [rncReceptor, setRncReceptor] = useState("");
    const [receptorNombre, setReceptorNombre] = useState("");
    const [receptorEmail, setReceptorEmail] = useState("");
    const [xmlSignedBase64, setXmlSignedBase64] = useState("");
    const [lineItems, setLineItems] = useState([
        { descripcion: "Servicio profesional", cantidad: "1", precioUnitario: "1500.00", itbisRate: "0.18" },
    ]);
    const [message, setMessage] = useState(null);
    const tutor = useFormTutor(EmitEcfTutorConfig);
    const total = useMemo(() => {
        return lineItems.reduce((acc, item) => {
            const qty = Number(item.cantidad || "0");
            const unit = Number(item.precioUnitario || "0");
            const rate = Number(item.itbisRate || "0");
            const subtotal = qty * unit;
            return acc + subtotal + subtotal * rate;
        }, 0);
    }, [lineItems]);
    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!hasPermission("TENANT_INVOICE_EMIT")) {
            setMessage("No tienes permisos para emitir e-CF.");
            return;
        }
        try {
            const result = await emitMutation.mutateAsync({
                encf: encf.trim() || null,
                tipoEcf,
                rncReceptor: rncReceptor.trim() || null,
                receptorNombre: receptorNombre.trim() || null,
                receptorEmail: receptorEmail.trim() || null,
                total,
                lineItems: lineItems.map((item) => ({
                    descripcion: item.descripcion,
                    cantidad: Number(item.cantidad || "0"),
                    precioUnitario: Number(item.precioUnitario || "0"),
                    itbisRate: Number(item.itbisRate || "0"),
                })),
                xmlSignedBase64: xmlSignedBase64.trim() || null,
            });
            setMessage(`e-CF enviado a DGII. ENCF: ${result.encf} (TrackId: ${result.trackId})`);
            setEncf("");
            setXmlSignedBase64("");
        }
        catch {
            setMessage("No se pudo emitir el e-CF. Revisa datos de factura y configuracion fiscal.");
        }
    };
    return (_jsx(RequirePermission, { anyOf: ["TENANT_INVOICE_EMIT"], children: _jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-1", children: [_jsxs("h1", { className: "text-2xl font-semibold text-white flex items-center gap-3", children: ["Emitir e-CF", !tutor.isActive && (_jsx("button", { onClick: tutor.restartTutor, className: "text-xs bg-slate-800 text-primary px-3 py-1 rounded-full border border-slate-700 hover:bg-slate-700 transition", children: "Iniciar Tutorial" }))] }), _jsx("p", { className: "text-sm text-slate-300", children: "Genera facturas con productos/servicios y secuencia DGII controlada." }), tutor.isActive && (_jsxs("div", { className: "bg-primary/10 border border-primary/30 p-4 rounded-xl mb-4 relative overflow-hidden", children: [_jsxs("div", { className: "flex justify-between items-start", children: [_jsxs("div", { children: [_jsx("h3", { className: "text-sm font-bold text-primary mb-1", children: tutor.config.title }), _jsx("p", { className: "text-xs text-slate-300 mb-3", children: tutor.config.description })] }), _jsx("button", { onClick: () => tutor.dismissTutor(true), className: "text-xs text-slate-400 hover:text-white underline", children: "Omitir y no volver a mostrar" })] }), _jsx("p", { className: "text-xs text-primary font-semibold", children: "Pasa el raton sobre los botones (?) para ayuda contextual." })] }))] }), _jsxs("form", { onSubmit: handleSubmit, className: "space-y-6 rounded-xl border border-border bg-slate-900/40 p-6", children: [_jsxs("div", { className: "grid grid-cols-1 gap-6 md:grid-cols-2", children: [_jsxs("label", { className: "block space-y-2 text-sm text-foreground", id: "tour-step-tipo-ecf", children: [_jsxs("span", { className: "font-semibold text-slate-200 flex items-center", children: ["Tipo de e-CF ", _jsx("span", { className: "text-red-400 ml-1", children: "*" }), tutor.isActive && tutor.getFieldHelper("tipo-ecf") && _jsx(TutorContextualIcon, { info: tutor.getFieldHelper("tipo-ecf") })] }), _jsxs("select", { value: tipoEcf, onChange: (event) => setTipoEcf(event.target.value), className: "w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none", required: true, children: [_jsx("option", { value: "31", children: "31 - e-CF Factura de Credito Fiscal" }), _jsx("option", { value: "32", children: "32 - e-CF Factura de Consumo" }), _jsx("option", { value: "33", children: "33 - e-CF Nota de Debito" }), _jsx("option", { value: "34", children: "34 - e-CF Nota de Credito" })] })] }), _jsxs("label", { className: "block space-y-2 text-sm text-foreground", id: "tour-step-rnc", children: [_jsxs("span", { className: "font-semibold text-slate-200 flex items-center", children: ["RNC o Cedula del Comprador ", _jsx("span", { className: "text-red-400 ml-1", children: "*" }), tutor.isActive && tutor.getFieldHelper("comprador-rnc") && _jsx(TutorContextualIcon, { info: tutor.getFieldHelper("comprador-rnc") })] }), _jsx("input", { type: "text", maxLength: 11, value: rncReceptor, onChange: (event) => setRncReceptor(event.target.value), className: "w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none", placeholder: "Ej: 101000000", required: true })] }), _jsxs("label", { className: "block space-y-2 text-sm text-foreground", id: "tour-step-monto", children: [_jsxs("span", { className: "font-semibold text-slate-200 flex items-center", children: ["Cobro Total (RD$) ", _jsx("span", { className: "text-red-400 ml-1", children: "*" }), tutor.isActive && tutor.getFieldHelper("total-monto") && _jsx(TutorContextualIcon, { info: tutor.getFieldHelper("total-monto") })] }), _jsx("input", { type: "number", step: "0.01", value: total.toFixed(2), readOnly: true, className: "w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none" })] }), _jsxs("label", { className: "block space-y-2 text-sm text-foreground", id: "tour-step-itbis", children: [_jsx("span", { className: "font-semibold text-slate-200", children: "ITBIS Facturado (RD$)" }), _jsx("input", { type: "number", step: "0.01", value: (total * 0.18).toFixed(2), readOnly: true, className: "w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none" })] })] }), _jsxs("div", { className: "space-y-3 rounded-md border border-slate-700 p-3", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsx("span", { className: "text-sm font-semibold text-slate-200", children: "Productos / Servicios" }), _jsx("button", { type: "button", className: "rounded border border-slate-700 px-2 py-1 text-xs text-slate-200", onClick: () => setLineItems((prev) => [
                                                ...prev,
                                                { descripcion: "", cantidad: "1", precioUnitario: "0.00", itbisRate: "0.18" },
                                            ]), children: "Agregar linea" })] }), lineItems.map((line, idx) => (_jsxs("div", { className: "grid grid-cols-1 gap-2 md:grid-cols-4", children: [_jsx("input", { value: line.descripcion, onChange: (event) => setLineItems((prev) => prev.map((row, i) => (i === idx ? { ...row, descripcion: event.target.value } : row))), className: "rounded-md border border-input bg-slate-950 px-3 py-2 text-sm", placeholder: "Descripcion" }), _jsx("input", { value: line.cantidad, onChange: (event) => setLineItems((prev) => prev.map((row, i) => (i === idx ? { ...row, cantidad: event.target.value } : row))), className: "rounded-md border border-input bg-slate-950 px-3 py-2 text-sm", type: "number", step: "0.01", placeholder: "Cantidad" }), _jsx("input", { value: line.precioUnitario, onChange: (event) => setLineItems((prev) => prev.map((row, i) => (i === idx ? { ...row, precioUnitario: event.target.value } : row))), className: "rounded-md border border-input bg-slate-950 px-3 py-2 text-sm", type: "number", step: "0.01", placeholder: "Precio unitario" }), _jsx("input", { value: line.itbisRate, onChange: (event) => setLineItems((prev) => prev.map((row, i) => (i === idx ? { ...row, itbisRate: event.target.value } : row))), className: "rounded-md border border-input bg-slate-950 px-3 py-2 text-sm", type: "number", step: "0.0001", placeholder: "ITBIS rate" })] }, `line-${idx}`)))] }), _jsxs("div", { className: "grid grid-cols-1 gap-4 md:grid-cols-3", children: [_jsx("input", { value: encf, onChange: (event) => setEncf(event.target.value), className: "rounded-md border border-input bg-slate-950 px-3 py-2 text-sm", placeholder: "ENCF manual (opcional)" }), _jsx("input", { value: receptorNombre, onChange: (event) => setReceptorNombre(event.target.value), className: "rounded-md border border-input bg-slate-950 px-3 py-2 text-sm", placeholder: "Nombre receptor" }), _jsx("input", { value: receptorEmail, onChange: (event) => setReceptorEmail(event.target.value), className: "rounded-md border border-input bg-slate-950 px-3 py-2 text-sm", placeholder: "Correo receptor", type: "email" })] }), _jsxs("label", { className: "block space-y-2 text-sm text-foreground", id: "tour-step-payload", children: [_jsx("span", { className: "font-semibold text-slate-200", children: "XML firmado en base64 (opcional)" }), _jsx("textarea", { value: xmlSignedBase64, onChange: (event) => setXmlSignedBase64(event.target.value), className: "h-32 w-full rounded-md border border-input bg-slate-950 px-3 py-2 font-mono text-xs focus:border-primary focus:outline-none", placeholder: "Pega aqui XML firmado si ya lo tienes." })] }), _jsxs("label", { className: "flex items-center gap-3 text-sm text-foreground", id: "tour-step-sync", children: [_jsx("input", { type: "checkbox", className: "h-4 w-4 rounded border-input bg-slate-950 text-primary accent-primary", defaultChecked: true }), _jsxs("span", { className: "font-semibold text-slate-200 flex items-center", children: ["Transmision agil (directa) a DGII", tutor.isActive && tutor.getFieldHelper("transmision-agil") && _jsx(TutorContextualIcon, { info: tutor.getFieldHelper("transmision-agil") })] })] }), _jsx("div", { className: "flex justify-end pt-4 border-t border-border", children: _jsx("button", { id: "tour-step-submit", className: "flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90", type: "submit", disabled: emitMutation.isPending, children: emitMutation.isPending ? _jsx(Spinner, { label: "Procesando Validacion" }) : "Validar y Emitir e-CF" }) })] }), message ? _jsx("p", { className: "text-sm text-emerald-300", children: message }) : null] }) }));
}
