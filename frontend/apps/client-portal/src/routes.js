import { jsx as _jsx } from "react/jsx-runtime";
import { Navigate, Outlet, createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { RequireAuth, RequireOnboardingComplete, RequireScope } from "./auth/guards";
import { DashboardPage } from "./pages/Dashboard";
import { InvoicesPage } from "./pages/Invoices";
import { InvoiceDetailPage } from "./pages/InvoiceDetail";
import { PlansPage } from "./pages/Plans";
import { AssistantPage } from "./pages/Assistant";
import { EmitECFPage } from "./pages/EmitECF";
import { RecurringInvoicesPage } from "./pages/RecurringInvoices";
import { EmitRFCEPage } from "./pages/EmitRFCE";
import { ApprovalsPage } from "./pages/Approvals";
import { CertificatesPage } from "./pages/Certificates";
import { OdooIntegrationPage } from "./pages/OdooIntegration";
import { ProfilePage } from "./pages/Profile";
import { LoginPage } from "./pages/Login";
import { MFAPage } from "./pages/MFA";
import { AuthCallbackPage } from "./pages/AuthCallback";
import { OnboardingPage } from "./pages/Onboarding";
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
        path: "/auth/callback",
        element: _jsx(AuthCallbackPage, {}),
    },
    {
        path: "/",
        element: (_jsx(RequireAuth, { children: _jsx(RequireScope, { scope: "TENANT", children: _jsx(AppLayout, {}) }) })),
        children: [
            { path: "onboarding", element: _jsx(OnboardingPage, {}) },
            {
                element: (_jsx(RequireOnboardingComplete, { children: _jsx(Outlet, {}) })),
                children: [
                    { path: "dashboard", element: _jsx(DashboardPage, {}) },
                    { path: "invoices", element: _jsx(InvoicesPage, {}) },
                    { path: "invoices/:id", element: _jsx(InvoiceDetailPage, {}) },
                    { path: "plans", element: _jsx(PlansPage, {}) },
                    { path: "assistant", element: _jsx(AssistantPage, {}) },
                    { path: "emit/ecf", element: _jsx(EmitECFPage, {}) },
                    { path: "recurring-invoices", element: _jsx(RecurringInvoicesPage, {}) },
                    { path: "emit/rfce", element: _jsx(EmitRFCEPage, {}) },
                    { path: "approvals", element: _jsx(ApprovalsPage, {}) },
                    { path: "certificates", element: _jsx(CertificatesPage, {}) },
                    { path: "integrations/odoo", element: _jsx(OdooIntegrationPage, {}) },
                    { path: "profile", element: _jsx(ProfilePage, {}) },
                ],
            },
        ],
    },
    {
        path: "*",
        element: _jsx(Navigate, { to: "/dashboard", replace: true }),
    },
]);
