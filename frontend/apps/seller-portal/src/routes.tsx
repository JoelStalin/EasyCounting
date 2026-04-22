import { Suspense, lazy, type ReactNode } from "react";
import { Navigate, createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { RequireAuth, RequirePermission, RequireScope } from "./auth/guards";

const DashboardPage = lazy(() => import("./pages/Dashboard").then((module) => ({ default: module.DashboardPage })));
const TenantsPage = lazy(() => import("./pages/Tenants").then((module) => ({ default: module.TenantsPage })));
const InvoicesPage = lazy(() => import("./pages/Invoices").then((module) => ({ default: module.InvoicesPage })));
const EmitECFPage = lazy(() => import("./pages/EmitECF").then((module) => ({ default: module.EmitECFPage })));
const ProfilePage = lazy(() => import("./pages/Profile").then((module) => ({ default: module.ProfilePage })));
const LoginPage = lazy(() => import("./pages/Login").then((module) => ({ default: module.LoginPage })));
const MFAPage = lazy(() => import("./pages/MFA").then((module) => ({ default: module.MFAPage })));
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
        <RequireScope scope="PARTNER">
          <AppLayout />
        </RequireScope>
      </RequireAuth>
    ),
    children: [
      { path: "dashboard", element: suspended(<DashboardPage />) },
      {
        path: "clients",
        element: (
          <RequirePermission anyOf={["PARTNER_TENANT_VIEW"]}>
            {suspended(<TenantsPage />)}
          </RequirePermission>
        ),
      },
      {
        path: "invoices",
        element: (
          <RequirePermission anyOf={["PARTNER_INVOICE_READ"]}>
            {suspended(<InvoicesPage />)}
          </RequirePermission>
        ),
      },
      {
        path: "emit/ecf",
        element: (
          <RequirePermission anyOf={["PARTNER_INVOICE_EMIT"]}>
            {suspended(<EmitECFPage />)}
          </RequirePermission>
        ),
      },
      { path: "profile", element: suspended(<ProfilePage />) },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);
