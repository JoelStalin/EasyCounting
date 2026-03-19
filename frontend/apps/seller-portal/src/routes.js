import { jsx as _jsx } from "react/jsx-runtime";
import { Navigate, createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { RequireAuth, RequirePermission, RequireScope } from "./auth/guards";
import { DashboardPage } from "./pages/Dashboard";
import { TenantsPage } from "./pages/Tenants";
import { InvoicesPage } from "./pages/Invoices";
import { EmitECFPage } from "./pages/EmitECF";
import { ProfilePage } from "./pages/Profile";
import { LoginPage } from "./pages/Login";
import { MFAPage } from "./pages/MFA";
export const router = createBrowserRouter([
    {
        path: "/",
        element: _jsx(Navigate, { to: "/dashboard", replace: true }),
    },
    {
        path: "/login",
        element: _jsx(LoginPage, {}),
    },
    {
        path: "/mfa",
        element: _jsx(MFAPage, {}),
    },
    {
        path: "/",
        element: (_jsx(RequireAuth, { children: _jsx(RequireScope, { scope: "PARTNER", children: _jsx(AppLayout, {}) }) })),
        children: [
            { path: "dashboard", element: _jsx(DashboardPage, {}) },
            {
                path: "clients",
                element: (_jsx(RequirePermission, { anyOf: ["PARTNER_TENANT_VIEW"], children: _jsx(TenantsPage, {}) })),
            },
            {
                path: "invoices",
                element: (_jsx(RequirePermission, { anyOf: ["PARTNER_INVOICE_READ"], children: _jsx(InvoicesPage, {}) })),
            },
            {
                path: "emit/ecf",
                element: (_jsx(RequirePermission, { anyOf: ["PARTNER_INVOICE_EMIT"], children: _jsx(EmitECFPage, {}) })),
            },
            { path: "profile", element: _jsx(ProfilePage, {}) },
        ],
    },
    {
        path: "*",
        element: _jsx(Navigate, { to: "/dashboard", replace: true }),
    },
]);
