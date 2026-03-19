import { Navigate, createBrowserRouter } from "react-router-dom";
import { SiteLayout } from "./components/SiteLayout";
import { HomePage } from "./pages/Home";
import { ProductsPage } from "./pages/Products";
import { AccountingManagementPage } from "./pages/AccountingManagement";
import { PlatformPage } from "./pages/Platform";
import { ContactPage } from "./pages/Contact";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <SiteLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "productos", element: <ProductsPage /> },
      { path: "productos/accounting-management", element: <AccountingManagementPage /> },
      { path: "plataforma", element: <PlatformPage /> },
      { path: "contacto", element: <ContactPage /> },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);
