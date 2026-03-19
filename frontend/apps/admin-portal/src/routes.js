import { jsx as _jsx } from "react/jsx-runtime";
import { Navigate, createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { RequireAuth, RequirePermission, RequireScope } from "./auth/guards";
import { DashboardPage } from "./pages/Dashboard";
import { CompaniesPage } from "./pages/Companies";
import { CompanyCertificatesTab, CompanyDetailLayout, CompanyInvoicesTab, CompanyOverviewTab, CompanyAccountingTab, CompanyPlansTab, CompanySettingsTab, CompanyUsersTab, } from "./pages/CompanyDetail";
import { PlansPage } from "./pages/Plans";
import { PlanEditorPage } from "./pages/PlanEditor";
import { AuditLogsPage } from "./pages/AuditLogs";
import { PlatformUsersPage } from "./pages/Users";
import { LoginPage } from "./pages/Login";
import { MFAPage } from "./pages/MFA";
import { AIProvidersPage } from "./pages/AIProviders";
import { AuthCallbackPage } from "./pages/AuthCallback";
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
        element: (_jsx(RequireAuth, { children: _jsx(RequireScope, { scope: "PLATFORM", children: _jsx(AppLayout, {}) }) })),
        children: [
            {
                path: "dashboard",
                element: _jsx(DashboardPage, {}),
            },
            {
                path: "companies",
                element: _jsx(CompaniesPage, {}),
            },
            {
                path: "companies/:id",
                element: _jsx(CompanyDetailLayout, {}),
                children: [
                    { index: true, element: _jsx(Navigate, { to: "overview", replace: true }) },
                    { path: "overview", element: _jsx(CompanyOverviewTab, {}) },
                    { path: "invoices", element: _jsx(CompanyInvoicesTab, {}) },
                    { path: "accounting", element: _jsx(CompanyAccountingTab, {}) },
                    { path: "plans", element: _jsx(CompanyPlansTab, {}) },
                    { path: "certificates", element: _jsx(CompanyCertificatesTab, {}) },
                    { path: "users", element: _jsx(CompanyUsersTab, {}) },
                    { path: "settings", element: _jsx(CompanySettingsTab, {}) },
                ],
            },
            {
                path: "plans",
                element: _jsx(PlansPage, {}),
            },
            {
                path: "ai-providers",
                element: (_jsx(RequirePermission, { anyOf: ["PLATFORM_AI_PROVIDER_MANAGE"], children: _jsx(AIProvidersPage, {}) })),
            },
            {
                path: "plans/new",
                element: _jsx(PlanEditorPage, {}),
            },
            {
                path: "audit-logs",
                element: _jsx(AuditLogsPage, {}),
            },
            {
                path: "users",
                element: _jsx(PlatformUsersPage, {}),
            },
        ],
    },
    {
        path: "*",
        element: _jsx(Navigate, { to: "/dashboard", replace: true }),
    },
]);
