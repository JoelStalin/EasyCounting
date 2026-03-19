import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreatePlan } from "../api/plans";
export function PlanEditorPage() {
    const navigate = useNavigate();
    const createPlan = useCreatePlan();
    const [form, setForm] = useState({
        name: "",
        precio_mensual: "0.00",
        precio_por_documento: "0.0000",
        documentos_incluidos: 0,
        max_facturas_mes: 0,
        max_facturas_por_receptor_mes: 0,
        max_monto_por_factura: "0.00",
        includes_recurring_invoices: false,
        descripcion: "",
    });
    const handleSubmit = async (event) => {
        event.preventDefault();
        await createPlan.mutateAsync({
            name: form.name,
            precio_mensual: form.precio_mensual,
            precio_por_documento: form.precio_por_documento,
            documentos_incluidos: Number(form.documentos_incluidos) || 0,
            max_facturas_mes: Number(form.max_facturas_mes) || 0,
            max_facturas_por_receptor_mes: Number(form.max_facturas_por_receptor_mes) || 0,
            max_monto_por_factura: form.max_monto_por_factura || "0.00",
            includes_recurring_invoices: form.includes_recurring_invoices,
            descripcion: form.descripcion ? form.descripcion : null,
        });
        navigate("/plans");
    };
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Editor de plan tarifario" }), _jsx("p", { className: "text-sm text-slate-300", children: "Configura valores fijos, porcentajes y tramos escalonados siguiendo las f\u00F3rmulas descritas en la gu\u00EDa 13." })] }), createPlan.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo guardar el plan." })) : null, _jsxs("form", { className: "space-y-4", onSubmit: handleSubmit, children: [_jsxs("div", { className: "grid gap-4 md:grid-cols-2", children: [_jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["Nombre del plan", _jsx("input", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", placeholder: "Plan Mixto Pro", value: form.name, onChange: (e) => setForm((prev) => ({ ...prev, name: e.target.value })) })] }), _jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["Incluidos", _jsx("input", { type: "number", className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", value: form.documentos_incluidos, onChange: (e) => setForm((prev) => ({ ...prev, documentos_incluidos: Number(e.target.value) })) })] })] }), _jsxs("div", { className: "grid gap-4 md:grid-cols-3", children: [_jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["M\u00E1x. facturas/mes", _jsx("input", { type: "number", className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", value: form.max_facturas_mes, onChange: (e) => setForm((prev) => ({ ...prev, max_facturas_mes: Number(e.target.value) })) })] }), _jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["M\u00E1x. facturas/cliente/mes", _jsx("input", { type: "number", className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", value: form.max_facturas_por_receptor_mes, onChange: (e) => setForm((prev) => ({ ...prev, max_facturas_por_receptor_mes: Number(e.target.value) })) })] }), _jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["M\u00E1x. monto por factura (DOP)", _jsx("input", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", value: form.max_monto_por_factura, onChange: (e) => setForm((prev) => ({ ...prev, max_monto_por_factura: e.target.value })) })] })] }), _jsxs("div", { className: "grid gap-4 md:grid-cols-3", children: [_jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["Precio mensual", _jsx("input", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", value: form.precio_mensual, onChange: (e) => setForm((prev) => ({ ...prev, precio_mensual: e.target.value })) })] }), _jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["Precio por documento", _jsx("input", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", value: form.precio_por_documento, onChange: (e) => setForm((prev) => ({ ...prev, precio_por_documento: e.target.value })) })] }), _jsxs("label", { className: "space-y-2 text-sm text-slate-300", children: ["Descripci\u00F3n", _jsx("input", { className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2", value: form.descripcion, onChange: (e) => setForm((prev) => ({ ...prev, descripcion: e.target.value })) })] })] }), _jsxs("label", { className: "flex items-center gap-3 rounded-md border border-slate-800 bg-slate-950/40 px-4 py-3 text-sm text-slate-200", children: [_jsx("input", { type: "checkbox", checked: form.includes_recurring_invoices, onChange: (e) => setForm((prev) => ({ ...prev, includes_recurring_invoices: e.target.checked })) }), "Incluir facturas recurrentes en este plan"] }), _jsxs("div", { className: "flex justify-end gap-2", children: [_jsx("button", { type: "button", className: "rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-200", children: "Cancelar" }), _jsx("button", { type: "submit", disabled: createPlan.isPending || !form.name, className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:bg-slate-700", children: createPlan.isPending ? "Guardando…" : "Guardar plan" })] })] })] }));
}
