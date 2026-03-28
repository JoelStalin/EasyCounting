import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { useEmitPartnerInvoice, usePartnerTenants } from "../api/partner";
function buildDemoEncf() {
    return `E31${Date.now().toString().slice(-9)}`;
}
export function EmitECFPage() {
    const tenantsQuery = usePartnerTenants();
    const emitMutation = useEmitPartnerInvoice();
    const availableTenants = useMemo(() => (tenantsQuery.data ?? []).filter((tenant) => tenant.canEmit), [tenantsQuery.data]);
    const [tenantId, setTenantId] = useState("");
    const [encf, setEncf] = useState(buildDemoEncf());
    const [tipoEcf, setTipoEcf] = useState("31");
    const [rncReceptor, setRncReceptor] = useState("101010101");
    const [total, setTotal] = useState("1250.00");
    const handleSubmit = async (event) => {
        event.preventDefault();
        await emitMutation.mutateAsync({
            tenantId: Number(tenantId),
            encf,
            tipoEcf,
            rncReceptor,
            total,
        });
        setEncf(buildDemoEncf());
    };
    return (_jsxs("div", { className: "grid gap-6 xl:grid-cols-[1.1fr,0.9fr]", children: [_jsxs(Card, { children: [_jsxs(CardHeader, { className: "space-y-2", children: [_jsx(CardTitle, { children: "Emisi\u00F3n demo controlada" }), _jsx("p", { className: "text-sm text-slate-300", children: "El socio solo puede generar documentos demo para clientes que tenga asignados con permiso de emisi\u00F3n." })] }), _jsx(CardContent, { children: _jsxs("form", { className: "space-y-4", onSubmit: handleSubmit, children: [_jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "tenantId", children: "Cliente" }), tenantsQuery.isLoading ? (_jsx("div", { "aria-live": "polite", className: "flex min-h-10 items-center rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-300", children: _jsx(Spinner, { label: "Cargando clientes habilitados" }) })) : (_jsxs("select", { id: "tenantId", className: "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100", value: tenantId, onChange: (event) => setTenantId(event.target.value), required: true, children: [_jsx("option", { value: "", children: "Selecciona un cliente" }), availableTenants.map((tenant) => (_jsxs("option", { value: tenant.id, children: [tenant.name, " \u00B7 ", tenant.rnc] }, tenant.id)))] }))] }), _jsxs("div", { className: "grid gap-4 md:grid-cols-2", children: [_jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "encf", children: "ENCF" }), _jsx(Input, { id: "encf", value: encf, onChange: (event) => setEncf(event.target.value), required: true })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "tipoEcf", children: "Tipo e-CF" }), _jsx(Input, { id: "tipoEcf", value: tipoEcf, onChange: (event) => setTipoEcf(event.target.value), required: true })] })] }), _jsxs("div", { className: "grid gap-4 md:grid-cols-2", children: [_jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "rncReceptor", children: "RNC receptor" }), _jsx(Input, { id: "rncReceptor", value: rncReceptor, onChange: (event) => setRncReceptor(event.target.value) })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "total", children: "Monto total" }), _jsx(Input, { id: "total", value: total, onChange: (event) => setTotal(event.target.value), required: true })] })] }), _jsx(Button, { className: "w-full", type: "submit", disabled: emitMutation.isPending || availableTenants.length === 0, children: emitMutation.isPending ? _jsx(Spinner, { label: "Generando" }) : "Generar comprobante demo" })] }) })] }), _jsxs(Card, { children: [_jsxs(CardHeader, { className: "space-y-2", children: [_jsx(CardTitle, { children: "Resultado y reglas" }), _jsx("p", { className: "text-sm text-slate-300", children: "Esta superficie est\u00E1 limitada por rol y por asignaci\u00F3n de clientes." })] }), _jsxs(CardContent, { className: "space-y-4 text-sm text-slate-300", children: [_jsxs("ul", { className: "space-y-2", children: [_jsx("li", { children: "\u2022 `partner_reseller` y `partner_operator` pueden emitir solo si la asignaci\u00F3n habilita `canEmit`." }), _jsx("li", { children: "\u2022 `partner_auditor` conserva acceso de lectura, sin emisi\u00F3n." }), _jsx("li", { children: "\u2022 Los documentos se crean en estado `SIMULADO` dentro del backend demo." })] }), emitMutation.isSuccess ? (_jsxs("div", { className: "rounded-xl border border-emerald-900/60 bg-emerald-950/30 p-4 text-emerald-200", children: [_jsx("p", { className: "font-medium", children: emitMutation.data.message }), _jsxs("p", { className: "mt-2 font-mono text-xs", children: ["Track: ", emitMutation.data.trackId] }), _jsxs("p", { className: "font-mono text-xs", children: ["ENCF: ", emitMutation.data.encf] })] })) : null, emitMutation.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-rose-200", children: "No se pudo generar el comprobante demo. Verifica el cliente seleccionado y tus permisos." })) : null, tenantsQuery.isLoading ? _jsx("p", { children: "Cargando clientes habilitados..." }) : null] })] })] }));
}
