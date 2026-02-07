import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { Link } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { FileDownloader } from "../components/FileDownloader";
import { useCreateTenant, useTenants } from "../api/tenants";
export function CompaniesPage() {
    const tenantsQuery = useTenants();
    const createTenant = useCreateTenant();
    const [open, setOpen] = useState(false);
    const [form, setForm] = useState({ name: "", rnc: "", env: "testecf" });
    const handleCreate = async () => {
        await createTenant.mutateAsync({
            name: form.name,
            rnc: form.rnc,
            env: form.env,
            dgii_base_ecf: null,
            dgii_base_fc: null,
        });
        setOpen(false);
        setForm({ name: "", rnc: "", env: "testecf" });
    };
    const rows = (tenantsQuery.data ?? []).map((tenant) => ({
        id: String(tenant.id),
        name: tenant.name,
        rnc: tenant.rnc,
        env: tenant.env,
        status: tenant.status,
    }));
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "flex items-center justify-between", children: [_jsxs("div", { children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Compa\u00F1\u00EDas" }), _jsx("p", { className: "text-sm text-slate-300", children: "Gestiona tenants, ambientes DGII y certificados." })] }), _jsx("button", { onClick: () => setOpen(true), className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90", children: "Crear compa\u00F1\u00EDa" })] }), tenantsQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo cargar el listado de compa\u00F1\u00EDas." })) : null, _jsx(DataTable, { data: rows, columns: [
                    {
                        header: "Compañía",
                        cell: (row) => (_jsxs("div", { className: "space-y-1", children: [_jsx(Link, { className: "text-sm font-semibold text-primary", to: `/companies/${row.id}`, children: row.name }), _jsxs("p", { className: "text-xs text-slate-400", children: ["RNC: ", row.rnc] })] })),
                    },
                    { header: "Ambiente", cell: (row) => _jsx("span", { className: "text-sm text-slate-200", children: row.env }) },
                    { header: "Estado", cell: (row) => _jsx("span", { className: "text-sm text-slate-200", children: row.status }) },
                    {
                        header: "Documentos",
                        cell: () => (_jsxs("div", { className: "flex gap-2", children: [_jsx(FileDownloader, { href: "#", label: "XML" }), _jsx(FileDownloader, { href: "#", label: "RI" })] })),
                    },
                ], emptyMessage: tenantsQuery.isLoading
                    ? "Cargando compañías…"
                    : tenantsQuery.isError
                        ? "Error cargando compañías"
                        : "Sin compañías registradas" }), open ? (_jsx("div", { className: "fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4", children: _jsxs("div", { className: "w-full max-w-lg space-y-4 rounded-xl border border-slate-800 bg-slate-950 p-6", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: "Crear compa\u00F1\u00EDa" }), _jsx("p", { className: "text-sm text-slate-400", children: "Registra un nuevo tenant y define el ambiente DGII." })] }), _jsxs("div", { className: "grid gap-3", children: [_jsxs("label", { className: "space-y-1 text-sm text-slate-300", children: ["Nombre", _jsx("input", { value: form.name, onChange: (e) => setForm((prev) => ({ ...prev, name: e.target.value })), className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" })] }), _jsxs("label", { className: "space-y-1 text-sm text-slate-300", children: ["RNC", _jsx("input", { value: form.rnc, onChange: (e) => setForm((prev) => ({ ...prev, rnc: e.target.value })), className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none" })] }), _jsxs("label", { className: "space-y-1 text-sm text-slate-300", children: ["Ambiente", _jsxs("select", { value: form.env, onChange: (e) => setForm((prev) => ({ ...prev, env: e.target.value })), className: "w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", children: [_jsx("option", { value: "testecf", children: "PRECERT (testecf)" }), _jsx("option", { value: "certecf", children: "CERT (certecf)" }), _jsx("option", { value: "ecf", children: "PROD (ecf)" })] })] })] }), createTenant.isError ? (_jsx("div", { className: "rounded-lg border border-rose-900/60 bg-rose-950/30 p-3 text-sm text-rose-200", children: "No se pudo crear la compa\u00F1\u00EDa. Verifica RNC y vuelve a intentar." })) : null, _jsxs("footer", { className: "flex justify-end gap-2", children: [_jsx("button", { onClick: () => setOpen(false), className: "rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-200", type: "button", children: "Cancelar" }), _jsx("button", { onClick: handleCreate, disabled: createTenant.isPending || !form.name || !form.rnc, className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:bg-slate-700", type: "button", children: createTenant.isPending ? "Creando…" : "Crear" })] })] }) })) : null] }));
}
