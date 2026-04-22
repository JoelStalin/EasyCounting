import { Suspense, lazy, type ReactNode } from "react";
import { Navigate, Outlet, createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { RequireAuth, RequireOnboardingComplete, RequireScope } from "./auth/guards";

const DashboardPage = lazy(() => import("./pages/Dashboard").then((module) => ({ default: module.DashboardPage })));
const InvoicesPage = lazy(() => import("./pages/Invoices").then((module) => ({ default: module.InvoicesPage })));
const InvoiceDetailPage = lazy(() =>
  import("./pages/InvoiceDetail").then((module) => ({ default: module.InvoiceDetailPage })),
);
const PlansPage = lazy(() => import("./pages/Plans").then((module) => ({ default: module.PlansPage })));
const AssistantPage = lazy(() => import("./pages/Assistant").then((module) => ({ default: module.AssistantPage })));
const EmitECFPage = lazy(() => import("./pages/EmitECF").then((module) => ({ default: module.EmitECFPage })));
const RecurringInvoicesPage = lazy(() =>
  import("./pages/RecurringInvoices").then((module) => ({ default: module.RecurringInvoicesPage })),
);
const EmitRFCEPage = lazy(() => import("./pages/EmitRFCE").then((module) => ({ default: module.EmitRFCEPage })));
const ApprovalsPage = lazy(() => import("./pages/Approvals").then((module) => ({ default: module.ApprovalsPage })));
const CertificatesPage = lazy(() =>
  import("./pages/Certificates").then((module) => ({ default: module.CertificatesPage })),
);
const OdooIntegrationPage = lazy(() =>
  import("./pages/OdooIntegration").then((module) => ({ default: module.OdooIntegrationPage })),
);
const ProfilePage = lazy(() => import("./pages/Profile").then((module) => ({ default: module.ProfilePage })));
const LoginPage = lazy(() => import("./pages/Login").then((module) => ({ default: module.LoginPage })));
const MFAPage = lazy(() => import("./pages/MFA").then((module) => ({ default: module.MFAPage })));
const AuthCallbackPage = lazy(() =>
  import("./pages/AuthCallback").then((module) => ({ default: module.AuthCallbackPage })),
);
const OnboardingPage = lazy(() =>
  import("./pages/Onboarding").then((module) => ({ default: module.OnboardingPage })),
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
        <RequireScope scope="TENANT">
          <AppLayout />
        </RequireScope>
      </RequireAuth>
    ),
    children: [
      { path: "onboarding", element: suspended(<OnboardingPage />) },
      {
        element: (
          <RequireOnboardingComplete>
            <Outlet />
          </RequireOnboardingComplete>
        ),
        children: [
          { path: "dashboard", element: suspended(<DashboardPage />) },
          { path: "invoices", element: suspended(<InvoicesPage />) },
          { path: "invoices/:id", element: suspended(<InvoiceDetailPage />) },
          { path: "plans", element: suspended(<PlansPage />) },
          { path: "assistant", element: suspended(<AssistantPage />) },
          { path: "emit/ecf", element: suspended(<EmitECFPage />) },
          { path: "recurring-invoices", element: suspended(<RecurringInvoicesPage />) },
          { path: "emit/rfce", element: suspended(<EmitRFCEPage />) },
          { path: "approvals", element: suspended(<ApprovalsPage />) },
          { path: "certificates", element: suspended(<CertificatesPage />) },
          { path: "integrations/odoo", element: suspended(<OdooIntegrationPage />) },
          { path: "profile", element: suspended(<ProfilePage />) },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);
