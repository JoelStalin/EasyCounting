import { Navigate, createBrowserRouter } from "react-router-dom";
import { SiteLayout } from "./components/SiteLayout";
import type { Locale } from "./site";
import { SiteProvider } from "./site-context";
import { EasyCountingPage } from "./pages/AccountingManagement";
import { CaseStudiesPage } from "./pages/CaseStudies";
import { CaseStudyDetailPage } from "./pages/CaseStudyDetail";
import { CompanyPage } from "./pages/Company";
import { ContactPage } from "./pages/Contact";
import { DiagnosticPage } from "./pages/Diagnostic";
import { HomePage } from "./pages/Home";
import { InsightsPage } from "./pages/Insights";
import { ProductsPage } from "./pages/Products";
import { ServiceDetailPage } from "./pages/ServiceDetail";
import { ServicesPage } from "./pages/Services";
import { SolutionsPage } from "./pages/Platform";

function createLocaleRoutes(locale: Locale) {
  const basePath = locale === "es" ? "/" : "/en";
  const company = locale === "es" ? "compania" : "company";
  const services = locale === "es" ? "servicios" : "services";
  const consulting = locale === "es" ? "consultoria" : "consulting";
  const implementation = locale === "es" ? "implementacion" : "implementation";
  const integrations = locale === "es" ? "integraciones" : "integrations";
  const digitalization = locale === "es" ? "digitalizacion" : "digitalization";
  const solutions = locale === "es" ? "soluciones" : "solutions";
  const products = locale === "es" ? "productos" : "products";
  const cases = locale === "es" ? "casos-de-exito" : "case-studies";
  const contact = locale === "es" ? "contacto" : "contact";
  const diagnostic = locale === "es" ? "diagnostico" : "diagnostic";

  return {
    path: basePath,
    element: (
      <SiteProvider locale={locale}>
        <SiteLayout />
      </SiteProvider>
    ),
    children: [
      { index: true, element: <HomePage />, handle: { pageKey: "home" } },
      { path: company, element: <CompanyPage />, handle: { pageKey: "company" } },
      { path: services, element: <ServicesPage />, handle: { pageKey: "services" } },
      { path: `${services}/${consulting}`, element: <ServiceDetailPage serviceKey="consulting" />, handle: { pageKey: "consulting" } },
      { path: `${services}/${implementation}`, element: <ServiceDetailPage serviceKey="implementation" />, handle: { pageKey: "implementation" } },
      { path: `${services}/${integrations}`, element: <ServiceDetailPage serviceKey="integrations" />, handle: { pageKey: "integrations" } },
      { path: `${services}/${digitalization}`, element: <ServiceDetailPage serviceKey="digitalization" />, handle: { pageKey: "digitalization" } },
      { path: solutions, element: <SolutionsPage />, handle: { pageKey: "solutions" } },
      { path: products, element: <ProductsPage />, handle: { pageKey: "products" } },
      { path: `${products}/easycounting`, element: <EasyCountingPage />, handle: { pageKey: "productDetail" } },
      { path: cases, element: <CaseStudiesPage />, handle: { pageKey: "cases" } },
      { path: `${cases}/galantes-jewelry`, element: <CaseStudyDetailPage caseId="galantes" />, handle: { pageKey: "caseGalantes" } },
      { path: `${cases}/chefalitas`, element: <CaseStudyDetailPage caseId="chefalitas" />, handle: { pageKey: "caseChefalitas" } },
      { path: "insights", element: <InsightsPage />, handle: { pageKey: "insights" } },
      { path: contact, element: <ContactPage />, handle: { pageKey: "contact" } },
      { path: diagnostic, element: <DiagnosticPage />, handle: { pageKey: "diagnostic" } },
    ],
  };
}

export const router = createBrowserRouter([
  createLocaleRoutes("en"),
  createLocaleRoutes("es"),
  {
    path: "/es/*",
    element: <Navigate to="/" replace />,
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);
