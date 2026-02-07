import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/use-auth";
const NAV = [
    { to: "/dashboard", label: "Dashboard", permissions: ["TENANT_INVOICE_READ"] },
    { to: "/invoices", label: "Comprobantes", permissions: ["TENANT_INVOICE_READ"] },
    { to: "/plans", label: "Planes", permissions: ["TENANT_PLAN_VIEW", "TENANT_PLAN_UPGRADE"] },
    { to: "/emit/ecf", label: "Emitir e-CF", permissions: ["TENANT_INVOICE_EMIT"] },
    { to: "/emit/rfce", label: "Emitir RFCE", permissions: ["TENANT_RFCE_SUBMIT"] },
    { to: "/approvals", label: "Aprobaciones", permissions: ["TENANT_APPROVAL_SEND"] },
    { to: "/certificates", label: "Certificados", permissions: ["TENANT_CERT_UPLOAD"] },
    { to: "/profile", label: "Perfil", permissions: [] },
];
export function AppLayout() {
    const { logout, user, permissions } = useAuth();
    return (_jsxs("div", { className: "flex min-h-screen bg-slate-950 text-slate-100", children: [_jsxs("aside", { className: "hidden w-64 border-r border-slate-900 bg-slate-950/80 p-6 md:block", children: [_jsxs("div", { className: "mb-8 space-y-1", children: [_jsx("h2", { className: "text-xl font-semibold text-white", children: "getupsoft Cliente" }), _jsx("p", { className: "text-xs text-slate-400", children: "Gesti\u00F3n de comprobantes y flujos DGII." })] }), _jsx("nav", { className: "space-y-2 text-sm", children: NAV.filter((item) => item.permissions.length === 0 || item.permissions.some((perm) => permissions.includes(perm))).map((item) => (_jsx(NavLink, { to: item.to, className: ({ isActive }) => `block rounded-md px-3 py-2 transition ${isActive ? "bg-primary/20 text-primary" : "text-slate-300 hover:bg-slate-900"}`, children: item.label }, item.to))) })] }), _jsxs("main", { className: "flex-1", children: [_jsxs("header", { className: "flex items-center justify-between border-b border-slate-900 bg-slate-950/60 px-6 py-4", children: [_jsxs("div", { children: [_jsx("p", { className: "text-xs uppercase tracking-wide text-slate-400", children: "Sesi\u00F3n" }), _jsx("p", { className: "text-sm font-medium text-slate-200", children: user?.email ?? "sin sesión" })] }), _jsx("button", { onClick: logout, className: "rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-primary hover:text-primary", children: "Salir" })] }), _jsx("div", { className: "px-6 py-8", children: _jsx(Outlet, {}) })] })] }));
}
