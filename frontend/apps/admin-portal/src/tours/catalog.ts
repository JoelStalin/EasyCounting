import type { GuidedTourStep } from "@getupsoft/ui";

export interface ViewTourDefinition {
  viewKey: string;
  patterns: string[];
  version: number;
  steps: GuidedTourStep[];
}

export const ADMIN_TOURS: ViewTourDefinition[] = [
  {
    viewKey: "admin-dashboard",
    patterns: ["/dashboard"],
    version: 1,
    steps: [
      { target: "h1", content: "Este panel resume el estado general de la plataforma." },
      { target: "[data-tour='portal-nav']", content: "Desde aqui navegas entre empresas, planes, usuarios y auditoria." },
      { target: "[data-tour='session-user']", content: "Aqui validas la cuenta activa y cierras sesion de forma segura." },
    ],
  },
  {
    viewKey: "admin-companies",
    patterns: ["/companies"],
    version: 1,
    steps: [
      { target: "h1", content: "Esta vista concentra la cartera multi-tenant administrada por plataforma." },
      { target: "[data-tour='portal-nav']", content: "El menu lateral te lleva al resto de modulos de gobierno." },
    ],
  },
  {
    viewKey: "admin-company-detail",
    patterns: ["/companies/:id/overview", "/companies/:id/invoices", "/companies/:id/accounting", "/companies/:id/plans", "/companies/:id/certificates", "/companies/:id/users", "/companies/:id/settings"],
    version: 1,
    steps: [
      { target: "h1", content: "Aqui administras una empresa especifica y sus parametros fiscales." },
      { target: "[data-tour='portal-nav']", content: "El contexto general de plataforma sigue disponible durante la edicion." },
    ],
  },
  {
    viewKey: "admin-plans",
    patterns: ["/plans", "/plans/new"],
    version: 1,
    steps: [
      { target: "h1", content: "Los planes controlan limites, precios y reglas comerciales del servicio." },
      { target: "[data-tour='tour-trigger']", content: "Puedes relanzar este tour manualmente desde el header." },
    ],
  },
  {
    viewKey: "admin-ai-providers",
    patterns: ["/ai-providers"],
    version: 1,
    steps: [
      { target: "h1", content: "Aqui se registran los proveedores IA cloud habilitados por superroot." },
      { target: "[data-tour='tour-trigger']", content: "Esta accion reabre el recorrido cuando necesites recordar el flujo." },
    ],
  },
  {
    viewKey: "admin-audit-logs",
    patterns: ["/audit-logs"],
    version: 1,
    steps: [
      { target: "h1", content: "La auditoria conserva trazabilidad operativa para cambios sensibles." },
      { target: "[data-tour='session-user']", content: "Confirma siempre la cuenta autenticada antes de revisar eventos." },
    ],
  },
  {
    viewKey: "admin-users",
    patterns: ["/users"],
    version: 1,
    steps: [
      { target: "h1", content: "Desde aqui gestionas usuarios internos de plataforma y sus roles." },
      { target: "[data-tour='portal-nav']", content: "Los permisos efectivos se reflejan tambien en la navegacion visible." },
    ],
  },
];
