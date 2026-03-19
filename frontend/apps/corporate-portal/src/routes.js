import { jsx as _jsx } from "react/jsx-runtime";
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
        element: _jsx(SiteLayout, {}),
        children: [
            { index: true, element: _jsx(HomePage, {}) },
            { path: "productos", element: _jsx(ProductsPage, {}) },
            { path: "productos/accounting-management", element: _jsx(AccountingManagementPage, {}) },
            { path: "plataforma", element: _jsx(PlatformPage, {}) },
            { path: "contacto", element: _jsx(ContactPage, {}) },
        ],
    },
    {
        path: "*",
        element: _jsx(Navigate, { to: "/", replace: true }),
    },
]);
