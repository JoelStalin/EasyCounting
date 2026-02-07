import { jsx as _jsx } from "react/jsx-runtime";
import { Navigate, createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { RequireAuth, RequireScope } from "./auth/guards";
import { DashboardPage } from "./pages/Dashboard";
import { InvoicesPage } from "./pages/Invoices";
import { InvoiceDetailPage } from "./pages/InvoiceDetail";
import { PlansPage } from "./pages/Plans";
import { EmitECFPage } from "./pages/EmitECF";
import { EmitRFCEPage } from "./pages/EmitRFCE";
import { ApprovalsPage } from "./pages/Approvals";
import { CertificatesPage } from "./pages/Certificates";
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
        element: (_jsx(RequireAuth, { children: _jsx(RequireScope, { scope: "TENANT", children: _jsx(AppLayout, {}) }) })),
        children: [
            { path: "dashboard", element: _jsx(DashboardPage, {}) },
            { path: "invoices", element: _jsx(InvoicesPage, {}) },
            { path: "invoices/:id", element: _jsx(InvoiceDetailPage, {}) },
            { path: "plans", element: _jsx(PlansPage, {}) },
            { path: "emit/ecf", element: _jsx(EmitECFPage, {}) },
            { path: "emit/rfce", element: _jsx(EmitRFCEPage, {}) },
            { path: "approvals", element: _jsx(ApprovalsPage, {}) },
            { path: "certificates", element: _jsx(CertificatesPage, {}) },
            { path: "profile", element: _jsx(ProfilePage, {}) },
        ],
    },
    {
        path: "*",
        element: _jsx(Navigate, { to: "/dashboard", replace: true }),
    },
]);
