import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useParams } from "react-router-dom";
import { useAccountingSummary, useCreateLedgerEntry, useLedgerEntries, useTenantSettings, useUpdateTenantSettings } from "../api/accounting";
import { useAdminInvoices } from "../api/dashboard";
import { useAssignTenantPlan, useTenant, useTenantPlan, useUpdateTenant } from "../api/tenants";
import { usePlans } from "../api/plans";
const TABS = [
    { to: "overview", label: "Resumen" },
    { to: "invoices", label: "Comprobantes" },
    { to: "accounting", label: "Contabilidad" },
    { to: "plans", label: "Planes" },
    { to: "certificates", label: "Certificados" },
    { to: "users", label: "Usuarios" },
    { to: "settings", label: "Parámetros" },
];
export function CompanyDetailLayout() {
    const { id } = useParams();
    const tenantQuery = useTenant(id);
    const tenant = tenantQuery.data;
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: tenantQuery.isLoading ? "Cargando compañía…" : tenant ? `Compañía: ${tenant.name}` : `Detalle de compañía #${id}` }), _jsx("p", { className: "text-sm text-slate-300", children: "Consulta comprobantes, planes tarifarios y equipos delegados." })] }), tenantQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo cargar el detalle de la compa\u00F1\u00EDa." })) : null, _jsx("nav", { className: "flex flex-wrap gap-3", children: TABS.map((tab) => (_jsx(NavLink, { to: tab.to, className: ({ isActive }) => `rounded-full border px-4 py-1 text-sm transition ${isActive ? "border-primary bg-primary/20 text-primary" : "border-slate-700 text-slate-300 hover:border-primary hover:text-primary"}`, children: tab.label }, tab.to))) }), _jsx("div", { className: "rounded-xl border border-slate-800 bg-slate-900/40 p-6", children: _jsx(Outlet, {}) })] }));
}
export function CompanyOverviewTab() {
    const { id } = useParams();
    const tenantQuery = useTenant(id);
    const tenant = tenantQuery.data;
    return (_jsxs("div", { className: "space-y-4 text-sm text-slate-300", children: [_jsxs("p", { children: ["RNC emisor: ", _jsx("span", { className: "font-mono text-slate-100", children: tenantQuery.isLoading ? "…" : tenant?.rnc ?? "—" })] }), _jsxs("p", { children: ["Ambiente actual: ", _jsx("span", { className: "font-semibold text-primary", children: tenantQuery.isLoading ? "…" : tenant?.env ?? "—" })] }), _jsx("p", { children: "\u00DAltima sincronizaci\u00F3n DGII: hace 12 minutos." })] }));
}
export function CompanyInvoicesTab() {
    const { id } = useParams();
    const tenantId = id ? Number(id) : undefined;
    const [estado, setEstado] = useState("");
    const [dateFrom, setDateFrom] = useState("");
    const [dateTo, setDateTo] = useState("");
    const [page, setPage] = useState(1);
    const invoicesQuery = useAdminInvoices({
        tenantId,
        page,
        size: 20,
        estado: estado || undefined,
        dateFrom: dateFrom ? `${dateFrom}T00:00:00` : undefined,
        dateTo: dateTo ? `${dateTo}T00:00:00` : undefined,
    });
    const invoices = invoicesQuery.data;
    const invoiceItems = invoices?.items ?? [];
    return (_jsxs("div", { className: "space-y-5", children: [_jsxs("div", { className: "grid gap-3 md:grid-cols-4", children: [_jsxs("div", { className: "space-y-1", children: [_jsx("label", { className: "text-xs uppercase tracking-wide text-slate-400", children: "Estado DGII" }), _jsxs("select", { value: estado, onChange: (event) => {
                                    setEstado(event.target.value);
                                    setPage(1);
                                }, className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", children: [_jsx("option", { value: "", children: "Todos" }), _jsx("option", { value: "ACEPTADO", children: "ACEPTADO" }), _jsx("option", { value: "RECHAZADO", children: "RECHAZADO" }), _jsx("option", { value: "pendiente", children: "pendiente" })] })] }), _jsxs("div", { className: "space-y-1", children: [_jsx("label", { className: "text-xs uppercase tracking-wide text-slate-400", children: "Desde" }), _jsx("input", { type: "date", value: dateFrom, onChange: (event) => {
                                    setDateFrom(event.target.value);
                                    setPage(1);
                                }, className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" })] }), _jsxs("div", { className: "space-y-1", children: [_jsx("label", { className: "text-xs uppercase tracking-wide text-slate-400", children: "Hasta" }), _jsx("input", { type: "date", value: dateTo, onChange: (event) => {
                                    setDateTo(event.target.value);
                                    setPage(1);
                                }, className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" })] }), _jsx("div", { className: "flex items-end justify-end", children: _jsx("button", { type: "button", onClick: () => {
                                setEstado("");
                                setDateFrom("");
                                setDateTo("");
                                setPage(1);
                            }, className: "rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-primary hover:text-primary", children: "Limpiar filtros" }) })] }), invoicesQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo cargar el listado de comprobantes." })) : null, _jsx("div", { className: "overflow-x-auto rounded-xl border border-slate-800", children: _jsxs("table", { className: "min-w-full divide-y divide-slate-800 text-sm text-slate-300", children: [_jsx("thead", { className: "bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400", children: _jsxs("tr", { children: [_jsx("th", { className: "px-3 py-2 text-left", children: "Fecha" }), _jsx("th", { className: "px-3 py-2 text-left", children: "ENCF" }), _jsx("th", { className: "px-3 py-2 text-left", children: "Tipo" }), _jsx("th", { className: "px-3 py-2 text-left", children: "TrackID" }), _jsx("th", { className: "px-3 py-2 text-left", children: "Estado DGII" }), _jsx("th", { className: "px-3 py-2 text-right", children: "Total" })] }) }), _jsxs("tbody", { children: [invoiceItems.map((item) => (_jsxs("tr", { className: "border-b border-slate-800/80 hover:bg-slate-900/40", children: [_jsx("td", { className: "px-3 py-2", children: new Date(item.fecha_emision).toLocaleString() }), _jsx("td", { className: "px-3 py-2 font-mono text-xs text-slate-400", children: item.encf }), _jsx("td", { className: "px-3 py-2", children: item.tipo_ecf }), _jsx("td", { className: "px-3 py-2 font-mono text-xs text-slate-400", children: item.track_id ?? "—" }), _jsx("td", { className: "px-3 py-2", children: item.estado_dgii }), _jsx("td", { className: "px-3 py-2 text-right", children: Number(item.total).toLocaleString("es-DO", {
                                                style: "currency",
                                                currency: "DOP",
                                            }) })] }, item.id))), invoicesQuery.isLoading ? (_jsx("tr", { children: _jsx("td", { className: "px-3 py-6 text-center text-sm text-slate-500", colSpan: 6, children: "Cargando comprobantes\u2026" }) })) : null, invoiceItems.length === 0 && !invoicesQuery.isLoading ? (_jsx("tr", { children: _jsx("td", { className: "px-3 py-6 text-center text-sm text-slate-500", colSpan: 6, children: "No hay comprobantes para los filtros actuales." }) })) : null] })] }) }), _jsxs("div", { className: "flex items-center justify-between text-xs text-slate-400", children: [_jsxs("span", { children: ["P\u00E1gina ", invoices?.page ?? page, " \u00B7 Total ", invoices?.total ?? 0] }), _jsxs("div", { className: "flex gap-2", children: [_jsx("button", { type: "button", onClick: () => setPage((p) => Math.max(1, p - 1)), disabled: page <= 1, className: "rounded-md border border-slate-700 px-3 py-1.5 font-semibold text-slate-200 disabled:cursor-not-allowed disabled:opacity-50", children: "Anterior" }), _jsx("button", { type: "button", onClick: () => setPage((p) => p + 1), disabled: invoiceItems.length < 20, className: "rounded-md border border-slate-700 px-3 py-1.5 font-semibold text-slate-200 disabled:cursor-not-allowed disabled:opacity-50", children: "Siguiente" })] })] })] }));
}
export function CompanyAccountingTab() {
    const { id } = useParams();
    const summaryQuery = useAccountingSummary(id);
    const ledgerQuery = useLedgerEntries(id);
    const createLedgerEntry = useCreateLedgerEntry(id);
    const [form, setForm] = useState({
        invoice_id: "",
        referencia: "",
        cuenta: "",
        descripcion: "",
        debit: "0.00",
        credit: "0.00",
        fecha: new Date().toISOString().slice(0, 16),
    });
    const handleChange = (event) => {
        const { name, value } = event.target;
        setForm((prev) => ({ ...prev, [name]: value }));
    };
    const handleSubmit = (event) => {
        event.preventDefault();
        createLedgerEntry.mutate({
            invoice_id: form.invoice_id ? Number(form.invoice_id) : null,
            referencia: form.referencia,
            cuenta: form.cuenta,
            descripcion: form.descripcion || null,
            debit: form.debit || "0",
            credit: form.credit || "0",
            fecha: new Date(form.fecha).toISOString(),
        });
    };
    const summary = summaryQuery.data;
    const ledger = ledgerQuery.data;
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("section", { className: "grid gap-4 sm:grid-cols-2 lg:grid-cols-4", children: [_jsx(StatCard, { label: "Total emitidos", value: summary?.totales.total_emitidos ?? 0 }), _jsx(StatCard, { label: "Aceptados", value: summary?.totales.total_aceptados ?? 0 }), _jsx(StatCard, { label: "Pendientes contables", value: summary?.contabilidad.pendientes ?? 0 }), _jsx(StatCard, { label: "Monto emitido", value: summary ? Number(summary.totales.total_monto).toLocaleString("es-DO", { style: "currency", currency: "DOP" }) : "RD$0.00", isCurrency: true })] }), _jsxs("section", { className: "space-y-3", children: [_jsx("h3", { className: "text-lg font-semibold text-white", children: "Registrar asiento" }), _jsxs("form", { onSubmit: handleSubmit, className: "grid gap-3 rounded-xl border border-slate-800 bg-slate-900/40 p-4 md:grid-cols-2", children: [_jsx("input", { name: "invoice_id", value: form.invoice_id, onChange: handleChange, placeholder: "ID del comprobante (opcional)", className: "rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }), _jsx("input", { required: true, name: "referencia", value: form.referencia, onChange: handleChange, placeholder: "Referencia contable", className: "rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }), _jsx("input", { required: true, name: "cuenta", value: form.cuenta, onChange: handleChange, placeholder: "Cuenta contable", className: "rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }), _jsx("input", { required: true, type: "datetime-local", name: "fecha", value: form.fecha, onChange: handleChange, className: "rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }), _jsx("input", { name: "debit", value: form.debit, onChange: handleChange, placeholder: "D\u00E9bito", className: "rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }), _jsx("input", { name: "credit", value: form.credit, onChange: handleChange, placeholder: "Cr\u00E9dito", className: "rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }), _jsx("textarea", { name: "descripcion", value: form.descripcion, onChange: handleChange, placeholder: "Descripci\u00F3n", className: "col-span-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", rows: 2 }), _jsx("div", { className: "col-span-full flex justify-end", children: _jsx("button", { type: "submit", className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700", disabled: createLedgerEntry.isPending, children: createLedgerEntry.isPending ? "Guardando…" : "Registrar asiento" }) })] })] }), _jsxs("section", { className: "space-y-3", children: [_jsxs("header", { className: "flex items-center justify-between", children: [_jsx("h3", { className: "text-lg font-semibold text-white", children: "Libro contable" }), _jsxs("p", { className: "text-xs text-slate-400", children: ["Mostrando ", ledger?.items.length ?? 0, " de ", ledger?.total ?? 0, " asientos"] })] }), _jsx("div", { className: "overflow-x-auto rounded-xl border border-slate-800", children: _jsxs("table", { className: "min-w-full divide-y divide-slate-800 text-sm text-slate-300", children: [_jsx("thead", { className: "bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400", children: _jsxs("tr", { children: [_jsx("th", { className: "px-3 py-2 text-left", children: "Fecha" }), _jsx("th", { className: "px-3 py-2 text-left", children: "Referencia" }), _jsx("th", { className: "px-3 py-2 text-left", children: "ENCF" }), _jsx("th", { className: "px-3 py-2 text-left", children: "Cuenta" }), _jsx("th", { className: "px-3 py-2 text-right", children: "D\u00E9bito" }), _jsx("th", { className: "px-3 py-2 text-right", children: "Cr\u00E9dito" })] }) }), _jsxs("tbody", { children: [ledger?.items.map((item) => (_jsxs("tr", { className: "border-b border-slate-800/80 hover:bg-slate-900/40", children: [_jsx("td", { className: "px-3 py-2", children: new Date(item.fecha).toLocaleString() }), _jsx("td", { className: "px-3 py-2 font-medium text-slate-100", children: item.referencia }), _jsx("td", { className: "px-3 py-2 font-mono text-xs text-slate-400", children: item.encf ?? "—" }), _jsx("td", { className: "px-3 py-2", children: item.cuenta }), _jsx("td", { className: "px-3 py-2 text-right text-emerald-300", children: Number(item.debit).toLocaleString("es-DO", { minimumFractionDigits: 2 }) }), _jsx("td", { className: "px-3 py-2 text-right text-rose-300", children: Number(item.credit).toLocaleString("es-DO", { minimumFractionDigits: 2 }) })] }, item.id))), ledger?.items.length === 0 && (_jsx("tr", { children: _jsx("td", { className: "px-3 py-6 text-center text-sm text-slate-500", colSpan: 6, children: "A\u00FAn no se registran asientos contables para esta empresa." }) })), !ledger && (_jsx("tr", { children: _jsx("td", { className: "px-3 py-6 text-center text-sm text-slate-500", colSpan: 6, children: "Cargando libro contable\u2026" }) }))] })] }) })] })] }));
}
export function CompanyPlansTab() {
    const { id } = useParams();
    const plansQuery = usePlans();
    const tenantPlanQuery = useTenantPlan(id);
    const assignPlan = useAssignTenantPlan(id);
    const [selectedPlanId, setSelectedPlanId] = useState("");
    useEffect(() => {
        const current = tenantPlanQuery.data?.plan?.id;
        setSelectedPlanId(current ? String(current) : "");
    }, [tenantPlanQuery.data?.plan?.id]);
    const currentPlanName = tenantPlanQuery.data?.plan?.name ?? "Sin plan asignado";
    return (_jsxs("div", { className: "space-y-4 text-sm text-slate-300", children: [_jsxs("p", { children: ["Plan vigente: ", _jsx("span", { className: "font-semibold text-primary", children: tenantPlanQuery.isLoading ? "Cargando…" : currentPlanName })] }), plansQuery.isError || tenantPlanQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo cargar la informaci\u00F3n de planes." })) : null, _jsxs("div", { className: "grid gap-3 rounded-xl border border-slate-800 bg-slate-900/40 p-4 md:grid-cols-3", children: [_jsxs("label", { className: "space-y-1 text-sm text-slate-200 md:col-span-2", children: ["Asignar plan", _jsxs("select", { value: selectedPlanId, onChange: (e) => setSelectedPlanId(e.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", disabled: plansQuery.isLoading || tenantPlanQuery.isLoading, children: [_jsx("option", { value: "", children: "Sin plan" }), (plansQuery.data ?? []).map((plan) => (_jsx("option", { value: String(plan.id), children: plan.name }, plan.id)))] })] }), _jsx("div", { className: "flex items-end justify-end", children: _jsx("button", { className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700", disabled: assignPlan.isPending, onClick: () => assignPlan.mutate(selectedPlanId ? Number(selectedPlanId) : null), type: "button", children: assignPlan.isPending ? "Guardando…" : "Guardar" }) })] })] }));
}
export function CompanyCertificatesTab() {
    return (_jsxs("div", { className: "space-y-4 text-sm text-slate-300", children: [_jsx("p", { children: "\u00DAltimo certificado subido: 2024-05-01." }), _jsx("button", { className: "rounded-md border border-dashed border-primary px-4 py-2 text-sm text-primary hover:bg-primary/10", children: "Subir .p12" })] }));
}
export function CompanyUsersTab() {
    return (_jsxs("div", { className: "space-y-4 text-sm text-slate-300", children: [_jsx("p", { children: "Usuarios delegados (RBAC multi-tenant) se mostrar\u00E1n aqu\u00ED." }), _jsx("button", { className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90", children: "Invitar usuario" })] }));
}
export function CompanySettingsTab() {
    const { id } = useParams();
    const tenantQuery = useTenant(id);
    const updateTenant = useUpdateTenant(id);
    const settingsQuery = useTenantSettings(id);
    const updateSettings = useUpdateTenantSettings(id);
    const [issuerForm, setIssuerForm] = useState({
        name: "",
        rnc: "",
    });
    const [settingsForm, setSettingsForm] = useState({
        moneda: "DOP",
        cuenta_ingresos: "",
        cuenta_itbis: "",
        cuenta_retenciones: "",
        dias_credito: 0,
        correo_facturacion: "",
        telefono_contacto: "",
        notas: "",
    });
    useEffect(() => {
        if (tenantQuery.data) {
            setIssuerForm({
                name: tenantQuery.data.name,
                rnc: tenantQuery.data.rnc,
            });
        }
    }, [tenantQuery.data]);
    useEffect(() => {
        if (settingsQuery.data) {
            setSettingsForm({
                moneda: settingsQuery.data.moneda,
                cuenta_ingresos: settingsQuery.data.cuenta_ingresos ?? "",
                cuenta_itbis: settingsQuery.data.cuenta_itbis ?? "",
                cuenta_retenciones: settingsQuery.data.cuenta_retenciones ?? "",
                dias_credito: settingsQuery.data.dias_credito,
                correo_facturacion: settingsQuery.data.correo_facturacion ?? "",
                telefono_contacto: settingsQuery.data.telefono_contacto ?? "",
                notas: settingsQuery.data.notas ?? "",
            });
        }
    }, [settingsQuery.data]);
    const handleIssuerChange = (event) => {
        const { name, value } = event.target;
        setIssuerForm((prev) => ({ ...prev, [name]: value }));
    };
    const handleSettingsChange = (event) => {
        const { name, value } = event.target;
        setSettingsForm((prev) => ({ ...prev, [name]: name === "dias_credito" ? Number(value) : value }));
    };
    const handleIssuerSubmit = (event) => {
        event.preventDefault();
        updateTenant.mutate({
            name: issuerForm.name,
            rnc: issuerForm.rnc,
        });
    };
    const handleSettingsSubmit = (event) => {
        event.preventDefault();
        updateSettings.mutate({
            moneda: settingsForm.moneda,
            cuenta_ingresos: settingsForm.cuenta_ingresos || null,
            cuenta_itbis: settingsForm.cuenta_itbis || null,
            cuenta_retenciones: settingsForm.cuenta_retenciones || null,
            dias_credito: settingsForm.dias_credito,
            correo_facturacion: settingsForm.correo_facturacion || null,
            telefono_contacto: settingsForm.telefono_contacto || null,
            notas: settingsForm.notas || null,
        });
    };
    return (_jsxs("div", { className: "space-y-8", children: [_jsxs("form", { onSubmit: handleIssuerSubmit, className: "grid gap-4 md:grid-cols-2", children: [_jsx(Field, { label: "Nombre / razon social del emisor", children: _jsx("input", { name: "name", value: issuerForm.name, onChange: handleIssuerChange, className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }) }), _jsx(Field, { label: "RNC del emisor", children: _jsx("input", { name: "rnc", value: issuerForm.rnc, onChange: handleIssuerChange, className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }) }), _jsx("div", { className: "md:col-span-2 flex justify-end gap-3", children: _jsx("button", { type: "submit", className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700", disabled: updateTenant.isPending, children: updateTenant.isPending ? "Guardando..." : "Guardar emisor" }) })] }), _jsxs("form", { onSubmit: handleSettingsSubmit, className: "grid gap-4 md:grid-cols-2", children: [_jsx(Field, { label: "Moneda", children: _jsx("input", { name: "moneda", value: settingsForm.moneda, onChange: handleSettingsChange, className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }) }), _jsx(Field, { label: "Dias de credito", children: _jsx("input", { name: "dias_credito", type: "number", min: 0, max: 365, value: settingsForm.dias_credito, onChange: handleSettingsChange, className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }) }), _jsx(Field, { label: "Cuenta de ingresos", children: _jsx("input", { name: "cuenta_ingresos", value: settingsForm.cuenta_ingresos, onChange: handleSettingsChange, placeholder: "701-VENT", className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }) }), _jsx(Field, { label: "Cuenta de ITBIS", children: _jsx("input", { name: "cuenta_itbis", value: settingsForm.cuenta_itbis, onChange: handleSettingsChange, placeholder: "208-ITBIS", className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }) }), _jsx(Field, { label: "Cuenta de retenciones", children: _jsx("input", { name: "cuenta_retenciones", value: settingsForm.cuenta_retenciones, onChange: handleSettingsChange, placeholder: "209-RET", className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }) }), _jsx(Field, { label: "Correo para facturacion", children: _jsx("input", { name: "correo_facturacion", value: settingsForm.correo_facturacion, onChange: handleSettingsChange, type: "email", placeholder: "facturacion@empresa.do", className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }) }), _jsx(Field, { label: "Telefono de contacto", children: _jsx("input", { name: "telefono_contacto", value: settingsForm.telefono_contacto, onChange: handleSettingsChange, placeholder: "809-555-0000", className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }) }), _jsx(Field, { label: "Notas internas", className: "md:col-span-2", children: _jsx("textarea", { name: "notas", value: settingsForm.notas, onChange: handleSettingsChange, rows: 3, className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" }) }), _jsxs("div", { className: "md:col-span-2 flex justify-end gap-3", children: [settingsQuery.data?.updated_at && (_jsxs("span", { className: "self-center text-xs text-slate-500", children: ["Ultima actualizacion: ", new Date(settingsQuery.data.updated_at).toLocaleString()] })), _jsx("button", { type: "submit", className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700", disabled: updateSettings.isPending, children: updateSettings.isPending ? "Guardando..." : "Guardar cambios" })] })] })] }));
}
function StatCard({ label, value, isCurrency }) {
    return (_jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-900/40 p-4", children: [_jsx("p", { className: "text-xs uppercase tracking-wide text-slate-400", children: label }), _jsx("p", { className: `mt-2 text-2xl font-semibold ${isCurrency ? "text-primary" : "text-slate-100"}`, children: value })] }));
}
function Field({ label, children, className }) {
    return (_jsxs("label", { className: `flex flex-col gap-1 text-sm text-slate-200 ${className ?? ""}`, children: [_jsx("span", { className: "text-xs uppercase tracking-wide text-slate-400", children: label }), children] }));
}
