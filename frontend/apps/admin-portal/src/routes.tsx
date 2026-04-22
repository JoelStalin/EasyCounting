import { Suspense, lazy, type ReactNode } from "react";
import { Navigate, createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { RequireAuth, RequirePermission, RequireScope } from "./auth/guards";

const DashboardPage = lazy(() => import("./pages/Dashboard").then((module) => ({ default: module.DashboardPage })));
const CompaniesPage = lazy(() => import("./pages/Companies").then((module) => ({ default: module.CompaniesPage })));
const CompanyDetailLayout = lazy(() =>
  import("./pages/CompanyDetail").then((module) => ({ default: module.CompanyDetailLayout })),
);
const CompanyOverviewTab = lazy(() =>
  import("./pages/CompanyDetail").then((module) => ({ default: module.CompanyOverviewTab })),
);
const CompanyInvoicesTab = lazy(() =>
  import("./pages/CompanyDetail").then((module) => ({ default: module.CompanyInvoicesTab })),
);
const CompanyAccountingTab = lazy(() =>
  import("./pages/CompanyDetail").then((module) => ({ default: module.CompanyAccountingTab })),
);
const CompanyPlansTab = lazy(() =>
  import("./pages/CompanyDetail").then((module) => ({ default: module.CompanyPlansTab })),
);
const CompanyCertificatesTab = lazy(() =>
  import("./pages/CompanyDetail").then((module) => ({ default: module.CompanyCertificatesTab })),
);
const CompanyUsersTab = lazy(() =>
  import("./pages/CompanyDetail").then((module) => ({ default: module.CompanyUsersTab })),
);
const CompanySettingsTab = lazy(() =>
  import("./pages/CompanyDetail").then((module) => ({ default: module.CompanySettingsTab })),
);
const PlansPage = lazy(() => import("./pages/Plans").then((module) => ({ default: module.PlansPage })));
const PlanEditorPage = lazy(() =>
  import("./pages/PlanEditor").then((module) => ({ default: module.PlanEditorPage })),
);
const AuditLogsPage = lazy(() => import("./pages/AuditLogs").then((module) => ({ default: module.AuditLogsPage })));
const PlatformUsersPage = lazy(() => import("./pages/Users").then((module) => ({ default: module.PlatformUsersPage })));
const LoginPage = lazy(() => import("./pages/Login").then((module) => ({ default: module.LoginPage })));
const MFAPage = lazy(() => import("./pages/MFA").then((module) => ({ default: module.MFAPage })));
const AIProvidersPage = lazy(() =>
  import("./pages/AIProviders").then((module) => ({ default: module.AIProvidersPage })),
);
const AuthCallbackPage = lazy(() =>
  import("./pages/AuthCallback").then((module) => ({ default: module.AuthCallbackPage })),
);

function suspended(element: ReactNode) {
  return (
    <Suspense fallback={<div className="flex min-h-[40vh] items-center justify-center text-sm text-slate-400">Cargando...</div>}>
      {element}
    </Suspense>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: "/login",
    element: suspended(<LoginPage />),
  },
  {
    path: "/mfa",
    element: suspended(<MFAPage />),
  },
  {
    path: "/auth/callback",
    element: suspended(<AuthCallbackPage />),
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
        element: suspended(<DashboardPage />),
      },
      {
        path: "companies",
        element: suspended(<CompaniesPage />),
      },
      {
        path: "companies/:id",
        element: suspended(<CompanyDetailLayout />),
        children: [
          { index: true, element: <Navigate to="overview" replace /> },
          { path: "overview", element: suspended(<CompanyOverviewTab />) },
          { path: "invoices", element: suspended(<CompanyInvoicesTab />) },
          { path: "accounting", element: suspended(<CompanyAccountingTab />) },
          { path: "plans", element: suspended(<CompanyPlansTab />) },
          { path: "certificates", element: suspended(<CompanyCertificatesTab />) },
          { path: "users", element: suspended(<CompanyUsersTab />) },
          { path: "settings", element: suspended(<CompanySettingsTab />) },
        ],
      },
      {
        path: "plans",
        element: suspended(<PlansPage />),
      },
      {
        path: "ai-providers",
        element: (
          <RequirePermission anyOf={["PLATFORM_AI_PROVIDER_MANAGE"]}>
            {suspended(<AIProvidersPage />)}
          </RequirePermission>
        ),
      },
      {
        path: "plans/new",
        element: suspended(<PlanEditorPage />),
      },
      {
        path: "audit-logs",
        element: suspended(<AuditLogsPage />),
      },
      {
        path: "users",
        element: suspended(<PlatformUsersPage />),
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);
