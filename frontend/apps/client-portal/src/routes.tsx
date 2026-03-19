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
    path: "/auth/callback",
    element: <AuthCallbackPage />,
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
      { path: "onboarding", element: <OnboardingPage /> },
      {
        element: (
          <RequireOnboardingComplete>
            <Outlet />
          </RequireOnboardingComplete>
        ),
        children: [
          { path: "dashboard", element: <DashboardPage /> },
          { path: "invoices", element: <InvoicesPage /> },
          { path: "invoices/:id", element: <InvoiceDetailPage /> },
          { path: "plans", element: <PlansPage /> },
          { path: "assistant", element: <AssistantPage /> },
          { path: "emit/ecf", element: <EmitECFPage /> },
          { path: "recurring-invoices", element: <RecurringInvoicesPage /> },
          { path: "emit/rfce", element: <EmitRFCEPage /> },
          { path: "approvals", element: <ApprovalsPage /> },
          { path: "certificates", element: <CertificatesPage /> },
          { path: "integrations/odoo", element: <OdooIntegrationPage /> },
          { path: "profile", element: <ProfilePage /> },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);
