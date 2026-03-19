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
        <RequireScope scope="PARTNER">
          <AppLayout />
        </RequireScope>
      </RequireAuth>
    ),
    children: [
      { path: "dashboard", element: <DashboardPage /> },
      {
        path: "clients",
        element: (
          <RequirePermission anyOf={["PARTNER_TENANT_VIEW"]}>
            <TenantsPage />
          </RequirePermission>
        ),
      },
      {
        path: "invoices",
        element: (
          <RequirePermission anyOf={["PARTNER_INVOICE_READ"]}>
            <InvoicesPage />
          </RequirePermission>
        ),
      },
      {
        path: "emit/ecf",
        element: (
          <RequirePermission anyOf={["PARTNER_INVOICE_EMIT"]}>
            <EmitECFPage />
          </RequirePermission>
        ),
      },
      { path: "profile", element: <ProfilePage /> },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);
