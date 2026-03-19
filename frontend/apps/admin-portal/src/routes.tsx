import { Navigate, createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { RequireAuth, RequirePermission, RequireScope } from "./auth/guards";
import { DashboardPage } from "./pages/Dashboard";
import { CompaniesPage } from "./pages/Companies";
import {
  CompanyCertificatesTab,
  CompanyDetailLayout,
  CompanyInvoicesTab,
  CompanyOverviewTab,
  CompanyAccountingTab,
  CompanyPlansTab,
  CompanySettingsTab,
  CompanyUsersTab,
} from "./pages/CompanyDetail";
import { PlansPage } from "./pages/Plans";
import { PlanEditorPage } from "./pages/PlanEditor";
import { AuditLogsPage } from "./pages/AuditLogs";
import { PlatformUsersPage } from "./pages/Users";
import { LoginPage } from "./pages/Login";
import { MFAPage } from "./pages/MFA";
import { AIProvidersPage } from "./pages/AIProviders";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/mfa",
    element: <MFAPage />,
  },
  {
    path: "/",
    element: (
      <RequireAuth>
        <RequireScope scope="PLATFORM">
          <AppLayout />
        </RequireScope>
      </RequireAuth>
    ),
    children: [
      {
        path: "dashboard",
        element: <DashboardPage />,
      },
      {
        path: "companies",
        element: <CompaniesPage />,
      },
      {
        path: "companies/:id",
        element: <CompanyDetailLayout />,
        children: [
          { index: true, element: <Navigate to="overview" replace /> },
          { path: "overview", element: <CompanyOverviewTab /> },
          { path: "invoices", element: <CompanyInvoicesTab /> },
          { path: "accounting", element: <CompanyAccountingTab /> },
          { path: "plans", element: <CompanyPlansTab /> },
          { path: "certificates", element: <CompanyCertificatesTab /> },
          { path: "users", element: <CompanyUsersTab /> },
          { path: "settings", element: <CompanySettingsTab /> },
        ],
      },
      {
        path: "plans",
        element: <PlansPage />,
      },
      {
        path: "ai-providers",
        element: (
          <RequirePermission anyOf={["PLATFORM_AI_PROVIDER_MANAGE"]}>
            <AIProvidersPage />
          </RequirePermission>
        ),
      },
      {
        path: "plans/new",
        element: <PlanEditorPage />,
      },
      {
        path: "audit-logs",
        element: <AuditLogsPage />,
      },
      {
        path: "users",
        element: <PlatformUsersPage />,
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);
