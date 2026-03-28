import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { RequirePermission } from "../auth/guards";
import { useInvoices } from "../api/invoices";
import { useCreateTenantApiToken, useRevokeTenantApiToken, useTenantApiTokens, } from "../api/tenant-api";
import { useOdooCustomers, useOdooInvoices, useOdooProducts, useOdooVendors, useSyncOdoo } from "../api/odoo-mirror";
function resolveEnterpriseApiBaseUrl() {
    const { hostname } = window.location;
    if (hostname === "127.0.0.1" || hostname === "localhost") {
        return "http://127.0.0.1:28080";
    }
    if (hostname === "getupsoft.com.do" || hostname.endsWith(".getupsoft.com.do")) {
        return "https://api.getupsoft.com.do";
    }
    return window.location.origin;
}
function formatDate(value) {
    if (!value) {
        return "Nunca";
    }
    return new Date(value).toLocaleString("es-DO");
}
function buildExampleCurl(baseUrl) {
    return [
        "curl -X POST \\",
        `  "${baseUrl}/api/v1/tenant-api/invoices" \\`,
        "  -H \"Authorization: Bearer <TOKEN_EMPRESARIAL>\" \\",
        "  -H \"Content-Type: application/json\" \\",
        "  -d '{",
        "    \"encf\": \"E310000000123\",",
        "    \"tipoEcf\": \"E31\",",
        "    \"rncReceptor\": \"131415161\",",
        "    \"total\": \"1500.00\"",
        "  }'",
    ].join("\n");
}
export function OdooIntegrationPage() {
    const [name, setName] = useState("Odoo ERP principal");
    const [accessMode, setAccessMode] = useState("read_write");
    const [expiresInDays, setExpiresInDays] = useState("365");
    const [latestToken, setLatestToken] = useState(null);
    const [errorMessage, setErrorMessage] = useState(null);
    const tokensQuery = useTenantApiTokens();
    const createToken = useCreateTenantApiToken();
    const revokeToken = useRevokeTenantApiToken();
    const invoicesQuery = useInvoices({ page: 1, size: 5 });
    const syncOdoo = useSyncOdoo();
    const customersQuery = useOdooCustomers(10);
    const vendorsQuery = useOdooVendors(10);
    const productsQuery = useOdooProducts(10);
    const odooInvoicesQuery = useOdooInvoices(10);
    const apiBaseUrl = useMemo(() => resolveEnterpriseApiBaseUrl(), []);
    const exampleCurl = useMemo(() => buildExampleCurl(apiBaseUrl), [apiBaseUrl]);
    async function handleCreateToken(event) {
        event.preventDefault();
        setErrorMessage(null);
        setLatestToken(null);
        try {
            const response = await createToken.mutateAsync({
                name: name.trim(),
                accessMode,
                expiresInDays: expiresInDays.trim() ? Number(expiresInDays) : null,
            });
            setLatestToken(response.token);
        }
        catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "No se pudo generar el token API.");
        }
    }
    async function handleRevoke(tokenId) {
        setErrorMessage(null);
        try {
            await revokeToken.mutateAsync(tokenId);
        }
        catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "No se pudo revocar el token API.");
        }
    }
    async function handleCopyToken() {
        if (!latestToken) {
            return;
        }
        await navigator.clipboard.writeText(latestToken);
    }
    return (_jsx(RequirePermission, { anyOf: ["TENANT_API_TOKEN_MANAGE"], children: _jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-2", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "API Odoo para clientes empresariales" }), _jsx("p", { className: "max-w-3xl text-sm text-slate-300", children: "Genera tokens API para que tu ERP Odoo consulte facturas, valide estados y registre comprobantes desde una integracion segura por tenant. Cada token queda aislado a tu empresa." })] }), errorMessage ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: errorMessage })) : null, latestToken ? (_jsxs("section", { className: "rounded-2xl border border-emerald-800/60 bg-emerald-950/20 p-5", children: [_jsxs("div", { className: "flex flex-wrap items-start justify-between gap-3", children: [_jsxs("div", { children: [_jsx("h2", { className: "text-lg font-semibold text-emerald-200", children: "Token generado" }), _jsx("p", { className: "text-sm text-emerald-100/80", children: "Este valor solo se muestra una vez. Copialo y guardalo en Odoo inmediatamente." })] }), _jsx("button", { type: "button", onClick: () => void handleCopyToken(), className: "rounded-md border border-emerald-700 px-3 py-2 text-xs font-semibold text-emerald-100 hover:bg-emerald-900/40", children: "Copiar token" })] }), _jsx("textarea", { readOnly: true, value: latestToken, rows: 3, className: "mt-4 w-full rounded-xl border border-emerald-900/60 bg-slate-950/70 px-3 py-3 font-mono text-sm text-emerald-100" })] })) : null, _jsxs("section", { className: "grid gap-6 xl:grid-cols-[1.1fr_0.9fr]", children: [_jsxs("form", { onSubmit: handleCreateToken, className: "space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6", "data-tour": "api-token-form", children: [_jsxs("div", { className: "space-y-1", children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: "Generar token empresarial" }), _jsx("p", { className: "text-sm text-slate-400", children: "Usa un token por integracion para revocar accesos sin afectar otros sistemas." })] }), _jsxs("label", { className: "block space-y-2", children: [_jsx("span", { className: "text-sm font-medium text-slate-200", children: "Nombre de la integracion" }), _jsx("input", { value: name, onChange: (event) => setName(event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", placeholder: "Odoo ERP principal", required: true })] }), _jsxs("div", { className: "grid gap-4 md:grid-cols-2", children: [_jsxs("label", { className: "block space-y-2", children: [_jsx("span", { className: "text-sm font-medium text-slate-200", children: "Acceso" }), _jsxs("select", { value: accessMode, onChange: (event) => setAccessMode(event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", children: [_jsx("option", { value: "read", children: "Solo lectura" }), _jsx("option", { value: "read_write", children: "Lectura y registro" })] })] }), _jsxs("label", { className: "block space-y-2", children: [_jsx("span", { className: "text-sm font-medium text-slate-200", children: "Expira en dias" }), _jsx("input", { value: expiresInDays, onChange: (event) => setExpiresInDays(event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", min: 1, max: 3650, type: "number" })] })] }), _jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-300", children: [_jsx("p", { className: "font-medium text-slate-100", children: "Scopes que recibira el token" }), _jsxs("ul", { className: "mt-2 space-y-1 text-slate-400", children: [_jsx("li", { children: "`invoices:read` para consultar listados y detalles." }), _jsx("li", { children: "`invoices:write` solo si quieres registrar facturas desde Odoo." })] })] }), _jsx("div", { className: "flex justify-end", children: _jsx("button", { type: "submit", disabled: createToken.isPending, className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700", children: createToken.isPending ? "Generando..." : "Generar token" }) })] }), _jsxs("section", { className: "space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6", "data-tour": "api-endpoints", children: [_jsxs("div", { className: "space-y-1", children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: "Endpoints para Odoo" }), _jsx("p", { className: "text-sm text-slate-400", children: "Esta base URL debe configurarse en tu cliente ERP para consumir el API empresarial por tenant." })] }), _jsxs("div", { className: "space-y-3 text-sm", children: [_jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-950/50 p-4", children: [_jsx("p", { className: "text-xs uppercase tracking-wide text-slate-400", children: "Base URL" }), _jsx("p", { className: "mt-2 break-all font-mono text-slate-100", children: apiBaseUrl })] }), _jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-950/50 p-4", children: [_jsx("p", { className: "text-xs uppercase tracking-wide text-slate-400", children: "Consultar facturas" }), _jsxs("p", { className: "mt-2 break-all font-mono text-slate-100", children: [apiBaseUrl, "/api/v1/tenant-api/invoices"] })] }), _jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-950/50 p-4", children: [_jsx("p", { className: "text-xs uppercase tracking-wide text-slate-400", children: "Registrar factura" }), _jsxs("p", { className: "mt-2 break-all font-mono text-slate-100", children: [apiBaseUrl, "/api/v1/tenant-api/invoices"] })] })] }), _jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-950/70 p-4", children: [_jsx("p", { className: "mb-3 text-xs uppercase tracking-wide text-slate-400", children: "Ejemplo curl" }), _jsx("pre", { className: "overflow-x-auto whitespace-pre-wrap text-xs text-slate-200", children: exampleCurl })] })] })] }), _jsxs("section", { className: "rounded-2xl border border-slate-800 bg-slate-900/40 p-6", "data-tour": "odoo-master-sync", children: [_jsxs("div", { className: "flex flex-wrap items-start justify-between gap-3", children: [_jsxs("div", { children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: "Sincronizacion Odoo completa" }), _jsx("p", { className: "text-sm text-slate-400", children: "Importa clientes, proveedores, productos y facturas desde Odoo 19 al hub EasyCounting." })] }), _jsx("button", { type: "button", onClick: () => void syncOdoo.mutateAsync({ includeCustomers: true, includeVendors: true, includeProducts: true, includeInvoices: true, limit: 100 }), disabled: syncOdoo.isPending, className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700", children: syncOdoo.isPending ? "Sincronizando..." : "Sincronizar ahora" })] }), syncOdoo.data ? (_jsxs("div", { className: "mt-4 rounded-xl border border-emerald-900/60 bg-emerald-950/20 p-4 text-sm text-emerald-200", children: [syncOdoo.data.message, " Clientes: ", syncOdoo.data.customers, ", Proveedores: ", syncOdoo.data.vendors, ", Productos:", " ", syncOdoo.data.products, ", Facturas: ", syncOdoo.data.invoices, "."] })) : null, _jsxs("div", { className: "mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4", children: [_jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-950/50 p-4", children: [_jsx("h3", { className: "text-sm font-semibold text-slate-100", children: "Clientes Odoo" }), _jsxs("p", { className: "mt-2 text-xs text-slate-400", children: [customersQuery.data?.length ?? 0, " registros locales."] })] }), _jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-950/50 p-4", children: [_jsx("h3", { className: "text-sm font-semibold text-slate-100", children: "Proveedores Odoo" }), _jsxs("p", { className: "mt-2 text-xs text-slate-400", children: [vendorsQuery.data?.length ?? 0, " registros locales."] })] }), _jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-950/50 p-4", children: [_jsx("h3", { className: "text-sm font-semibold text-slate-100", children: "Productos Odoo" }), _jsxs("p", { className: "mt-2 text-xs text-slate-400", children: [productsQuery.data?.length ?? 0, " registros locales."] })] }), _jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-950/50 p-4", children: [_jsx("h3", { className: "text-sm font-semibold text-slate-100", children: "Facturas Odoo" }), _jsxs("p", { className: "mt-2 text-xs text-slate-400", children: [odooInvoicesQuery.data?.length ?? 0, " registros locales."] })] })] })] }), _jsxs("section", { className: "rounded-2xl border border-slate-800 bg-slate-900/40 p-6", "data-tour": "api-token-list", children: [_jsxs("div", { children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: "Tokens emitidos" }), _jsx("p", { className: "text-sm text-slate-400", children: "Revoca cualquier token comprometido sin cerrar la sesion del portal." })] }), _jsxs("div", { className: "mt-4 space-y-3", children: [(tokensQuery.data ?? []).map((token) => (_jsx("article", { className: "rounded-xl border border-slate-800 bg-slate-950/50 p-4", children: _jsxs("div", { className: "flex flex-wrap items-start justify-between gap-3", children: [_jsxs("div", { className: "space-y-1", children: [_jsxs("div", { className: "flex flex-wrap items-center gap-2", children: [_jsx("h3", { className: "text-sm font-semibold text-slate-100", children: token.name }), token.revokedAt ? (_jsx("span", { className: "rounded-full bg-rose-500/15 px-2 py-0.5 text-[11px] font-semibold text-rose-300", children: "Revocado" })) : (_jsx("span", { className: "rounded-full bg-emerald-500/15 px-2 py-0.5 text-[11px] font-semibold text-emerald-300", children: "Activo" }))] }), _jsxs("p", { className: "text-xs text-slate-400", children: ["Prefijo: ", _jsx("span", { className: "font-mono text-slate-200", children: token.tokenPrefix }), " · ", "Scopes: ", _jsx("span", { className: "text-slate-200", children: token.scopes.join(", ") })] }), _jsxs("p", { className: "text-xs text-slate-500", children: ["Creado: ", formatDate(token.createdAt), " \u00B7 Ultimo uso: ", formatDate(token.lastUsedAt), " \u00B7 Expira:", " ", formatDate(token.expiresAt)] })] }), !token.revokedAt ? (_jsx("button", { type: "button", onClick: () => void handleRevoke(token.id), disabled: revokeToken.isPending, className: "rounded-md border border-rose-800 px-3 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-900/40", children: "Revocar" })) : null] }) }, token.id))), !tokensQuery.isLoading && (tokensQuery.data ?? []).length === 0 ? (_jsx("div", { className: "rounded-xl border border-dashed border-slate-800 p-6 text-sm text-slate-400", children: "Todavia no hay tokens API emitidos para este tenant." })) : null] })] }), _jsxs("section", { className: "rounded-2xl border border-slate-800 bg-slate-900/40 p-6", children: [_jsxs("div", { className: "space-y-1", children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: "Ultimos comprobantes visibles por el cliente" }), _jsx("p", { className: "text-sm text-slate-400", children: "Esta vista te deja validar rapidamente que la integracion Odoo y el portal observan el mismo tenant." })] }), _jsxs("div", { className: "mt-4 overflow-x-auto", children: [_jsxs("table", { className: "min-w-full divide-y divide-slate-800 text-sm", children: [_jsx("thead", { children: _jsxs("tr", { className: "text-left text-xs uppercase tracking-wide text-slate-400", children: [_jsx("th", { className: "pb-3 pr-4 font-medium", children: "ENCF" }), _jsx("th", { className: "pb-3 pr-4 font-medium", children: "Tipo" }), _jsx("th", { className: "pb-3 pr-4 font-medium", children: "Estado" }), _jsx("th", { className: "pb-3 pr-4 font-medium", children: "Total" }), _jsx("th", { className: "pb-3 font-medium", children: "Fecha" })] }) }), _jsx("tbody", { className: "divide-y divide-slate-900/80", children: (invoicesQuery.data?.items ?? []).map((invoice) => (_jsxs("tr", { className: "text-slate-200", children: [_jsx("td", { className: "py-3 pr-4 font-mono text-xs", children: invoice.encf }), _jsx("td", { className: "py-3 pr-4", children: invoice.tipo_ecf }), _jsx("td", { className: "py-3 pr-4", children: invoice.estado_dgii }), _jsx("td", { className: "py-3 pr-4", children: Number(invoice.total).toLocaleString("es-DO", { style: "currency", currency: "DOP" }) }), _jsx("td", { className: "py-3", children: new Date(invoice.fecha_emision).toLocaleString("es-DO") })] }, invoice.id))) })] }), !invoicesQuery.isLoading && (invoicesQuery.data?.items.length ?? 0) === 0 ? (_jsx("div", { className: "rounded-xl border border-dashed border-slate-800 p-6 text-sm text-slate-400", children: "No hay comprobantes recientes para mostrar en este tenant." })) : null] })] })] }) }));
}
