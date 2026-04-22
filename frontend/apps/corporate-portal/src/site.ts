export type Locale = "es" | "en";

export type PageKey =
  | "home"
  | "company"
  | "services"
  | "consulting"
  | "implementation"
  | "integrations"
  | "digitalization"
  | "solutions"
  | "products"
  | "productDetail"
  | "cases"
  | "caseGalantes"
  | "caseChefalitas"
  | "insights"
  | "contact"
  | "diagnostic";

type LinkItem = {
  label: string;
  description?: string;
  href?: string;
  page?: PageKey;
};

type CaseStudy = {
  id: "galantes" | "chefalitas";
  client: string;
  industry: string;
  headline: string;
  summary: string;
  challenge: string;
  intervention: string[];
  outcome: string[];
  evidence: string;
};

type ServicePageKey = "consulting" | "implementation" | "integrations" | "digitalization";

export type SiteContent = {
  localeName: string;
  switchLabel: string;
  ui: {
    languageSuggestion: string;
    languageSuggestionAction: string;
    headerTagline: string;
    homeProductsCta: string;
    companyPrinciplesLabel: string;
    productsPrimaryCta: string;
    productIncludesLabel: string;
    productAudienceLabel: string;
    productOutcomesLabel: string;
    productNextStepLabel: string;
    productNextStepTitle: string;
    productPortalClientLabel: string;
    productPortalAdminLabel: string;
    productDiagnosticCta: string;
    serviceViewDetailLabel: string;
    serviceCapabilitiesLabel: string;
    serviceOutcomesLabel: string;
    serviceIdealForLabel: string;
    casesChallengeLabel: string;
    casesInterventionLabel: string;
    casesReadMoreLabel: string;
    caseContextLabel: string;
    caseEvidenceLabel: string;
    caseInterventionDetailLabel: string;
    caseOutcomeLabel: string;
    contactChannelsLabel: string;
    contactJourneyLabel: string;
    contactOpenLabel: string;
    diagnosticIncludesLabel: string;
    diagnosticQuestionsLabel: string;
    diagnosticCtaLabel: string;
    diagnosticCtaDescription: string;
    diagnosticCtaButton: string;
  };
  navigation: Array<{ page: Exclude<PageKey, "productDetail" | "caseGalantes" | "caseChefalitas">; label: string }>;
  meta: Record<PageKey, { title: string; description: string }>;
  hero: {
    eyebrow: string;
    title: string;
    description: string;
    primaryCta: string;
    secondaryCta: string;
  };
  homeStats: Array<{ label: string; value: string }>;
  homeTrust: string[];
  company: {
    eyebrow: string;
    title: string;
    description: string;
    pillars: Array<{ title: string; description: string }>;
    principles: string[];
  };
  services: {
    eyebrow: string;
    title: string;
    description: string;
    items: Array<{ title: string; summary: string; bullets: string[]; page?: ServicePageKey }>;
  };
  serviceDetails: Record<
    ServicePageKey,
    {
      eyebrow: string;
      title: string;
      description: string;
      capabilities: string[];
      outcomes: string[];
      idealFor: string[];
      cta: string;
    }
  >;
  leadForm: {
    eyebrow: string;
    title: string;
    description: string;
    fields: {
      name: string;
      company: string;
      email: string;
      interest: string;
      market: string;
      challenge: string;
    };
    placeholders: {
      name: string;
      company: string;
      email: string;
      challenge: string;
    };
    interests: string[];
    markets: string[];
    submit: string;
  };
  solutions: {
    eyebrow: string;
    title: string;
    description: string;
    segments: Array<{ title: string; summary: string; bullets: string[] }>;
  };
  products: {
    eyebrow: string;
    title: string;
    description: string;
    items: Array<{ title: string; type: string; summary: string; bullets: string[] }>;
  };
  productDetail: {
    eyebrow: string;
    title: string;
    description: string;
    includes: string[];
    audiences: string[];
    outcomes: string[];
  };
  cases: {
    eyebrow: string;
    title: string;
    description: string;
    items: CaseStudy[];
  };
  insights: {
    eyebrow: string;
    title: string;
    description: string;
    pillars: Array<{ title: string; summary: string }>;
  };
  contact: {
    eyebrow: string;
    title: string;
    description: string;
    channels: LinkItem[];
    journeys: Array<{ title: string; description: string }>;
  };
  diagnostic: {
    eyebrow: string;
    title: string;
    description: string;
    includes: string[];
    checkpoints: string[];
  };
  footer: {
    description: string;
    columns: Array<{ title: string; links: LinkItem[] }>;
  };
};

export const SUPPORTED_LOCALES: Locale[] = ["es", "en"];

const PATHS: Record<Locale, Record<PageKey, string>> = {
  es: {
    home: "/",
    company: "/compania",
    services: "/servicios",
    consulting: "/servicios/consultoria",
    implementation: "/servicios/implementacion",
    integrations: "/servicios/integraciones",
    digitalization: "/servicios/digitalizacion",
    solutions: "/soluciones",
    products: "/productos",
    productDetail: "/productos/easycounting",
    cases: "/casos-de-exito",
    caseGalantes: "/casos-de-exito/galantes-jewelry",
    caseChefalitas: "/casos-de-exito/chefalitas",
    insights: "/insights",
    contact: "/contacto",
    diagnostic: "/diagnostico",
  },
  en: {
    home: "/en",
    company: "/en/company",
    services: "/en/services",
    consulting: "/en/services/consulting",
    implementation: "/en/services/implementation",
    integrations: "/en/services/integrations",
    digitalization: "/en/services/digitalization",
    solutions: "/en/solutions",
    products: "/en/products",
    productDetail: "/en/products/easycounting",
    cases: "/en/case-studies",
    caseGalantes: "/en/case-studies/galantes-jewelry",
    caseChefalitas: "/en/case-studies/chefalitas",
    insights: "/en/insights",
    contact: "/en/contact",
    diagnostic: "/en/diagnostic",
  },
};

export function buildPath(locale: Locale, page: PageKey): string {
  return PATHS[locale][page];
}

const casesEs: CaseStudy[] = [
  {
    id: "galantes",
    client: "Galante's Jewelry",
    industry: "Retail de lujo / joyeria",
    headline: "Rebranding premium con presencia digital conectada a operacion real.",
    summary:
      "Reposicionamiento de marca, experiencia web y activacion de catalogo conectado para una joyeria orientada a experiencia concierge.",
    challenge:
      "La marca necesitaba comunicar una propuesta premium de forma coherente, mostrar su oferta con elegancia y habilitar una base digital que no se quedara solo en vitrina.",
    intervention: [
      "Redefinicion de narrativa comercial y presencia digital.",
      "Construccion de experiencia web alineada al posicionamiento premium.",
      "Conexion del sitio con catalogo Odoo para visibilidad operativa en tiempo real.",
    ],
    outcome: [
      "Mejor demostracion de la propuesta de valor y del servicio concierge.",
      "Canal digital consistente con la identidad de marca.",
      "Base operativa para evolucion comercial y futuras integraciones.",
    ],
    evidence:
      "El sitio publico expone una narrativa premium y una coleccion viva conectada a catalogo operativo.",
  },
  {
    id: "chefalitas",
    client: "Chefalitas",
    industry: "Restauracion / consumo",
    headline: "Digitalizacion de marca gastronomica con estructura comercial lista para operar.",
    summary:
      "Transformacion de presencia digital para una marca gastronomica, ordenando narrativa, oferta y experiencia comercial.",
    challenge:
      "La marca necesitaba una base digital capaz de presentar mejor su propuesta, soportar crecimiento y ordenar la comunicacion con clientes.",
    intervention: [
      "Estructura de experiencia digital y presencia de marca.",
      "Implementacion del sitio y organizacion de contenido comercial.",
      "Acompañamiento tecnologico para una operacion mas clara y escalable.",
    ],
    outcome: [
      "Mejor presentacion comercial de la marca.",
      "Base digital lista para visibilidad, contacto y evolucion operativa.",
      "Proyecto demostrable como evidencia de ejecucion en rebranding + implementacion.",
    ],
    evidence:
      "El sitio publico funciona como presencia comercial activa y prueba de acompanamiento de implementacion real.",
  },
];

const casesEn: CaseStudy[] = [
  {
    ...casesEs[0],
    industry: "Luxury retail / jewelry",
    headline: "Premium rebrand with a digital presence tied to real operations.",
    summary:
      "Brand repositioning, web experience, and connected catalog activation for a concierge-oriented jewelry business.",
    challenge:
      "The brand needed to communicate a premium positioning clearly, showcase its offer elegantly, and build a digital foundation that went beyond a static showcase.",
    intervention: [
      "Commercial narrative and digital positioning redesign.",
      "Website experience aligned with the premium brand promise.",
      "Odoo-connected catalog visibility to support day-to-day operations.",
    ],
    outcome: [
      "Stronger articulation of value and concierge service.",
      "Digital channel aligned with the brand identity.",
      "Operational base for future commercial and integration growth.",
    ],
    evidence:
      "The live site combines premium storytelling with a product collection connected to operational catalog data.",
  },
  {
    ...casesEs[1],
    industry: "Restaurant / food service",
    headline: "Digital brand foundation for a restaurant concept ready to operate and grow.",
    summary:
      "Digital presence transformation for a food brand, structuring the narrative, offer, and commercial experience.",
    challenge:
      "The company needed a digital base able to present its concept clearly, support growth, and improve how customers engage with the brand.",
    intervention: [
      "Digital experience structure and brand presence design.",
      "Site implementation and organization of commercial content.",
      "Technology guidance to support a clearer and more scalable operation.",
    ],
    outcome: [
      "Stronger commercial brand presentation.",
      "A usable digital foundation for visibility, contact, and operational evolution.",
      "A tangible proof point of execution in rebranding plus implementation.",
    ],
    evidence:
      "The public site is a live commercial asset and a real example of implemented digital transformation work.",
  },
];

export const SITE_CONTENT: Record<Locale, SiteContent> = {
  es: {
    localeName: "ES",
    switchLabel: "English",
    ui: {
      languageSuggestion: "Prefieres ver este sitio en ingles?",
      languageSuggestionAction: "Cambiar a English",
      headerTagline: "Digitalizacion, implementacion y operacion",
      homeProductsCta: "Ver productos",
      companyPrinciplesLabel: "Principios",
      productsPrimaryCta: "Ver EasyCounting",
      productIncludesLabel: "Incluye",
      productAudienceLabel: "Para quien",
      productOutcomesLabel: "Resultado esperado",
      productNextStepLabel: "Siguiente paso",
      productNextStepTitle: "Explora el producto o agenda una conversacion de implementacion.",
      productPortalClientLabel: "Ver portal cliente",
      productPortalAdminLabel: "Ver portal admin",
      productDiagnosticCta: "Solicitar diagnostico",
      serviceViewDetailLabel: "Ver servicio",
      serviceCapabilitiesLabel: "Capacidades",
      serviceOutcomesLabel: "Resultado",
      serviceIdealForLabel: "Ideal para",
      casesChallengeLabel: "Desafio",
      casesInterventionLabel: "Intervencion",
      casesReadMoreLabel: "Ver caso completo",
      caseContextLabel: "Problema / contexto",
      caseEvidenceLabel: "Evidencia actual",
      caseInterventionDetailLabel: "Intervencion de GetUpSoft",
      caseOutcomeLabel: "Transformacion lograda",
      contactChannelsLabel: "Canales",
      contactJourneyLabel: "Como iniciar",
      contactOpenLabel: "Abrir",
      diagnosticIncludesLabel: "Incluye",
      diagnosticQuestionsLabel: "Preguntas clave",
      diagnosticCtaLabel: "CTA",
      diagnosticCtaDescription:
        "Usa este flujo para iniciar una conversacion orientada a arquitectura, prioridades y capacidad real de ejecucion.",
      diagnosticCtaButton: "Escribir a ventas",
    },
    navigation: [
      { page: "home", label: "Inicio" },
      { page: "company", label: "Compañia" },
      { page: "services", label: "Servicios" },
      { page: "solutions", label: "Soluciones" },
      { page: "products", label: "Productos" },
      { page: "cases", label: "Casos" },
      { page: "insights", label: "Insights" },
      { page: "contact", label: "Contacto" },
      { page: "diagnostic", label: "Diagnostico" },
    ],
    meta: {
      home: {
        title: "GetUpSoft | Digitalizacion, implementacion y operacion tecnologica",
        description:
          "GetUpSoft acompaña a empresas en digitalizacion, implementacion, integraciones, operacion y productos propios como EasyCounting.",
      },
      company: {
        title: "Compañia | GetUpSoft",
        description:
          "Conoce a GetUpSoft como empresa de transformacion digital, implementacion, integracion y operacion de tecnologia.",
      },
      services: {
        title: "Servicios | GetUpSoft",
        description:
          "Consultoria, implementacion, automatizacion, integraciones, soporte operativo y desarrollo a medida para empresas.",
      },
      consulting: {
        title: "Consultoria de digitalizacion | GetUpSoft",
        description: "Consultoria ejecutiva y operativa para priorizar arquitectura, procesos y roadmap de digitalizacion.",
      },
      implementation: {
        title: "Implementacion tecnologica | GetUpSoft",
        description: "Implementacion por fases de plataformas, portales y procesos digitales con handover operativo.",
      },
      integrations: {
        title: "Integraciones y automatizacion | GetUpSoft",
        description: "Integraciones entre ERP, producto, correo, documentos y flujos internos para reducir friccion.",
      },
      digitalization: {
        title: "Digitalizacion corporativa | GetUpSoft",
        description: "Rebranding digital, experiencias web y captacion comercial alineadas a la operacion real.",
      },
      solutions: {
        title: "Soluciones | GetUpSoft",
        description:
          "Soluciones para digitalizacion comercial, operacion fiscal, integraciones y plataformas empresariales.",
      },
      products: {
        title: "Productos | GetUpSoft",
        description:
          "Explora EasyCounting y la capa de activos productizados que GetUpSoft usa para acelerar implementaciones reales.",
      },
      productDetail: {
        title: "EasyCounting | Producto GetUpSoft",
        description:
          "EasyCounting es el producto propio de GetUpSoft para control fiscal, operativo y contable con soporte de implementacion.",
      },
      cases: {
        title: "Casos de exito | GetUpSoft",
        description:
          "Revisa proyectos ejecutados por GetUpSoft para clientes reales como Galante's Jewelry y Chefalitas.",
      },
      caseGalantes: {
        title: "Caso de exito: Galante's Jewelry | GetUpSoft",
        description:
          "Caso real de rebranding premium, experiencia digital e integracion operativa para Galante's Jewelry.",
      },
      caseChefalitas: {
        title: "Caso de exito: Chefalitas | GetUpSoft",
        description:
          "Caso real de digitalizacion, estructura comercial e implementacion web para Chefalitas.",
      },
      insights: {
        title: "Insights | GetUpSoft",
        description:
          "Ideas, guias y aprendizajes sobre digitalizacion, implementacion, integraciones y operacion empresarial.",
      },
      contact: {
        title: "Contacto | GetUpSoft",
        description:
          "Contacta a GetUpSoft para evaluar proyectos de digitalizacion, implementacion, soporte o productos propios.",
      },
      diagnostic: {
        title: "Diagnostico inicial | GetUpSoft",
        description:
          "Solicita un diagnostico inicial para definir prioridades, riesgos y hoja de ruta de transformacion digital.",
      },
    },
    hero: {
      eyebrow: "Consultoria, implementacion y productos digitales",
      title: "Convertimos estrategia digital en sistemas, operacion y crecimiento.",
      description:
        "GetUpSoft acompaña a empresas en digitalizacion, integracion, automatizacion, soporte operativo y desarrollo de soluciones propias y a medida. EasyCounting es parte del portafolio, no el limite de la compañia.",
      primaryCta: "Solicitar diagnostico",
      secondaryCta: "Ver casos reales",
    },
    homeStats: [
      { label: "Enfoque", value: "Servicios + implementacion + operacion + productos" },
      { label: "Capacidad", value: "Rebranding, digitalizacion, integraciones y acompanamiento" },
      { label: "Prueba real", value: "Clientes con proyectos ejecutados y activos en produccion" },
    ],
    homeTrust: [
      "Consultoria de digitalizacion",
      "Implementacion tecnologica",
      "Integraciones Odoo / DGII",
      "Operacion y soporte post-lanzamiento",
    ],
    company: {
      eyebrow: "Compañia",
      title: "Una empresa de tecnologia orientada a ejecucion real.",
      description:
        "No vendemos solo software. Diagnosticamos, acompañamos, implementamos, integramos y operamos soluciones para que la transformacion digital se convierta en un sistema sostenible.",
      pillars: [
        {
          title: "Acompañamiento estrategico",
          description:
            "Traducimos objetivos del negocio en prioridades, roadmap, arquitectura y decisiones tecnologicas concretas.",
        },
        {
          title: "Implementacion con ownership",
          description:
            "Diseñamos y construimos la solucion, conectamos herramientas y dejamos capacidad operativa real.",
        },
        {
          title: "Operacion continua",
          description:
            "No soltamos el proyecto al lanzar. Acompañamos soporte, evolucion, observabilidad y estabilizacion.",
        },
      ],
      principles: [
        "Estrategia sin ejecucion no transforma.",
        "Los productos propios aceleran, pero no sustituyen el criterio consultivo.",
        "Cada implementacion debe quedar operable, medible y mantenible.",
      ],
    },
    services: {
      eyebrow: "Servicios",
      title: "Capacidades que van de la definicion a la operacion.",
      description:
        "Organizamos la oferta para vender servicios y productos con claridad, diferenciando acompañamiento, implementacion y soporte.",
      items: [
        {
          title: "Consultoria de digitalizacion",
          summary: "Evaluacion de procesos, madurez, herramientas y oportunidades de automatizacion.",
          bullets: ["Diagnostico actual", "Roadmap priorizado", "Definicion de arquitectura objetivo"],
          page: "consulting",
        },
        {
          title: "Implementacion tecnologica",
          summary: "Puesta en operacion de plataformas, portales, integraciones y procesos digitales.",
          bullets: ["Configuracion e implantacion", "Rollout por fases", "Handover operativo"],
          page: "implementation",
        },
        {
          title: "Integraciones y automatizacion",
          summary: "Conexion de ERPs, flujos comerciales, correo, documentos y sistemas de soporte.",
          bullets: ["Odoo / DGII", "Automatizacion de procesos", "Sincronizacion entre herramientas"],
          page: "integrations",
        },
        {
          title: "Digitalizacion comercial",
          summary: "Experiencias digitales, presencia web y conversion conectadas a la operacion del negocio.",
          bullets: ["Sitios corporativos", "Rebranding digital", "Captacion y activacion comercial"],
          page: "digitalization",
        },
        {
          title: "Soporte y operacion",
          summary: "Acompañamiento posterior al lanzamiento para continuidad, monitoreo y mejora.",
          bullets: ["Runbooks", "Soporte funcional", "Estabilizacion y mejora continua"],
        },
      ],
    },
    serviceDetails: {
      consulting: {
        eyebrow: "Consultoria",
        title: "Consultoria de digitalizacion con criterio de negocio y arquitectura.",
        description:
          "Entramos primero a ordenar el problema: procesos, stack actual, restricciones, ownership, roadmap y riesgos de implementacion.",
        capabilities: [
          "Discovery ejecutivo y operativo.",
          "Mapa de procesos, sistemas y fricciones.",
          "Arquitectura objetivo y prioridades por fase.",
        ],
        outcomes: [
          "Decisiones mejor priorizadas.",
          "Menos retrabajo en implementacion.",
          "Una hoja de ruta util para negocio y tecnologia.",
        ],
        idealFor: [
          "Empresas que aun no tienen claro por donde empezar.",
          "Organizaciones con herramientas dispersas y poca visibilidad.",
          "Equipos que quieren alinear liderazgo y ejecucion tecnica.",
        ],
        cta: "Solicitar consultoria inicial",
      },
      implementation: {
        eyebrow: "Implementacion",
        title: "Implementacion tecnologica con ownership y salida operativa real.",
        description:
          "No solo configuramos software: implantamos procesos, conectamos flujos y dejamos una operacion utilizable por el equipo.",
        capabilities: [
          "Rollout por fases y entregables claros.",
          "Configuracion de producto, portales y workflows.",
          "Transferencia operativa y estabilizacion posterior.",
        ],
        outcomes: [
          "Menor tiempo a operacion.",
          "Menos dependencia del proveedor para tareas rutinarias.",
          "Mejor adopcion interna del sistema.",
        ],
        idealFor: [
          "Empresas que ya decidieron la direccion y necesitan ejecucion.",
          "Equipos que requieren producto + integracion + soporte.",
          "Proyectos que no pueden quedarse solo en demo o piloto.",
        ],
        cta: "Iniciar implementacion",
      },
      integrations: {
        eyebrow: "Integraciones",
        title: "Integraciones y automatizacion para unir producto, ERP y operacion.",
        description:
          "Diseñamos puentes entre plataformas, ERPs, correo, documentos y flujos internos para reducir friccion operativa.",
        capabilities: [
          "Integraciones con Odoo, DGII y herramientas internas.",
          "Automatizacion de tareas repetitivas y flujos de soporte.",
          "Sincronizacion entre fuentes de datos y canales.",
        ],
        outcomes: [
          "Menos doble digitacion.",
          "Mas trazabilidad entre areas.",
          "Procesos mas rapidos y auditables.",
        ],
        idealFor: [
          "Equipos con silos entre comercial, finanzas y operacion.",
          "Empresas que ya usan ERP y necesitan capas complementarias.",
          "Operaciones con procesos manuales frecuentes.",
        ],
        cta: "Evaluar integraciones",
      },
      digitalization: {
        eyebrow: "Digitalizacion",
        title: "Digitalizacion comercial y corporativa para presentar, captar y operar mejor.",
        description:
          "Combinamos marca, experiencia digital y estructura operativa para que la presencia online tenga impacto comercial real.",
        capabilities: [
          "Sitios corporativos y experiencias de marca.",
          "Rebranding digital y organizacion de contenido comercial.",
          "Formularios, captacion y journeys conectados a operacion.",
        ],
        outcomes: [
          "Mejor posicionamiento corporativo.",
          "Mayor claridad comercial al vender servicios y productos.",
          "Una base digital mas coherente con la operacion real.",
        ],
        idealFor: [
          "Empresas que crecieron sin una narrativa corporativa clara.",
          "Marcas que necesitan pasar de presencia basica a canal comercial real.",
          "Negocios que quieren vender mejor servicios, productos o ambos.",
        ],
        cta: "Explorar digitalizacion",
      },
    },
    leadForm: {
      eyebrow: "Formulario",
      title: "Cuéntanos tu contexto.",
      description: "Usa este formulario para iniciar un diagnostico, una implementacion o una conversacion comercial mas precisa.",
      fields: {
        name: "Nombre",
        company: "Empresa",
        email: "Correo",
        interest: "Interes principal",
        market: "Mercado / contexto",
        challenge: "Que necesitas resolver",
      },
      placeholders: {
        name: "Tu nombre",
        company: "Nombre de la empresa",
        email: "tu@empresa.com",
        challenge: "Describe el proceso, problema o proyecto que quieres resolver.",
      },
      interests: [
        "Consultoria de digitalizacion",
        "Implementacion tecnologica",
        "Integraciones y automatizacion",
        "Digitalizacion corporativa",
        "Producto EasyCounting",
      ],
      markets: ["Republica Dominicana", "Latinoamerica", "Operacion regional", "Otro mercado"],
      submit: "Enviar por correo",
    },
    solutions: {
      eyebrow: "Soluciones",
      title: "Tecnologia organizada alrededor de retos de negocio.",
      description:
        "La empresa debe vender resultados: control operativo, visibilidad, integracion y crecimiento sostenible.",
      segments: [
        {
          title: "Operacion fiscal y contable",
          summary: "Capas para cumplimiento, trazabilidad y gestion administrativa.",
          bullets: ["Facturacion electronica", "Conciliacion e integracion contable", "Seguimiento documental"],
        },
        {
          title: "Digitalizacion comercial",
          summary: "Experiencias web, presencia de marca y flujos de captacion conectados a operacion.",
          bullets: ["Rebranding digital", "Sitios corporativos", "Portales y formularios comerciales"],
        },
        {
          title: "Integracion empresarial",
          summary: "Puentes entre producto, ERP, automatizacion y herramientas internas.",
          bullets: ["Sincronizacion de catalogos", "Integracion de canales", "Automatizacion de backoffice"],
        },
      ],
    },
    products: {
      eyebrow: "Productos",
      title: "Productos propios y activos productizados para acelerar implementaciones.",
      description:
        "EasyCounting es el producto principal. Alrededor de el, GetUpSoft ofrece activos reutilizables e implementacion consultiva.",
      items: [
        {
          title: "EasyCounting",
          type: "Producto propio",
          summary: "Plataforma para control fiscal, operativo y contable con enfoque multi-tenant e integraciones.",
          bullets: ["Emision y seguimiento", "Portales por rol", "Integraciones y gobierno operativo"],
        },
        {
          title: "Aceleradores de implementacion",
          type: "Activos productizados",
          summary: "Componentes, procesos y playbooks que reducen tiempo de salida a produccion.",
          bullets: ["Templates operativos", "Integraciones base", "Capas de despliegue y observabilidad"],
        },
        {
          title: "Soluciones a medida",
          type: "Servicio con base reusable",
          summary: "Construimos extensiones y nuevos modulos cuando el negocio requiere mas que un producto cerrado.",
          bullets: ["Portales privados", "Workflows personalizados", "Capas de automatizacion"],
        },
      ],
    },
    productDetail: {
      eyebrow: "Producto destacado",
      title: "EasyCounting: producto propio para control fiscal y operativo con acompañamiento real.",
      description:
        "EasyCounting debe presentarse como parte del portafolio de la empresa: un producto fuerte, pero apoyado por consultoria, implementacion e integracion.",
      includes: [
        "Portales para administracion, clientes y socios.",
        "Operacion fiscal, documental y contable en una sola base.",
        "Integracion con Odoo y procesos de soporte a cumplimiento.",
      ],
      audiences: [
        "Empresas con necesidades de control administrativo y trazabilidad.",
        "Firmas operativas que requieren multiempresa y roles diferenciados.",
        "Equipos que necesitan producto + implementacion + soporte.",
      ],
      outcomes: [
        "Menos friccion en operacion diaria.",
        "Mejor visibilidad de cumplimiento y evidencia.",
        "Capacidad de crecer con integraciones y modulos nuevos.",
      ],
    },
    cases: {
      eyebrow: "Casos reales",
      title: "Clientes atendidos y proyectos ejecutados.",
      description:
        "Galante's Jewelry y Chefalitas no son referencias estéticas: son evidencia real de rebranding, digitalizacion e implementacion entregada por la empresa.",
      items: casesEs,
    },
    insights: {
      eyebrow: "Insights",
      title: "Contenido para vender criterio, no solo tecnologia.",
      description:
        "El sitio corporativo debe crecer con contenido localizado que posicione a GetUpSoft en digitalizacion, integracion y operacion.",
      pillars: [
        { title: "Transformacion digital aplicada", summary: "Roadmaps, priorizacion y decision de arquitectura con impacto real." },
        { title: "Implementacion e integraciones", summary: "Lecciones sobre despliegues, adopcion y operacion entre sistemas." },
        { title: "Productos y operacion", summary: "Como conectar software propio con procesos, soporte y crecimiento comercial." },
      ],
    },
    contact: {
      eyebrow: "Contacto",
      title: "Conversemos sobre digitalizacion, implementacion o producto.",
      description:
        "El objetivo del contacto no es solo pedir una demo. Tambien debe servir para proyectos de integracion, desarrollo y acompañamiento estrategico.",
      channels: [
        { label: "ventas@getupsoft.com", description: "Oportunidades comerciales y diagnosticos", href: "mailto:ventas@getupsoft.com" },
        { label: "info@getupsoft.com", description: "Contacto general y alianzas", href: "mailto:info@getupsoft.com" },
        { label: "EasyCounting", description: "Explorar el producto", href: "https://easycounting.getupsoft.com" },
      ],
      journeys: [
        { title: "Demo de producto", description: "Para equipos que ya necesitan evaluar EasyCounting en detalle." },
        { title: "Diagnostico inicial", description: "Para empresas que necesitan definir primero problema, arquitectura y prioridades." },
        { title: "Implementacion / integraciones", description: "Para proyectos donde el producto es solo una parte de la solucion." },
      ],
    },
    diagnostic: {
      eyebrow: "Diagnostico inicial",
      title: "Una primera conversacion para ordenar el problema antes de construir.",
      description:
        "La mejor entrada comercial para la empresa es un diagnostico guiado: situacion actual, restricciones, stack, riesgos y objetivos.",
      includes: [
        "Reunion de discovery con foco en negocio y operacion.",
        "Mapa de sistemas actuales, procesos y fricciones.",
        "Hipotesis de solucion, riesgos y siguientes pasos recomendados.",
      ],
      checkpoints: [
        "Que proceso quieres digitalizar o estabilizar.",
        "Que sistemas ya existen y cuales deben integrarse.",
        "Que resultados necesitas en 30, 60 y 90 dias.",
      ],
    },
    footer: {
      description:
        "GetUpSoft combina consultoria, implementacion, integracion, operacion y productos propios para ejecutar transformacion digital con seriedad corporativa.",
      columns: [
        {
          title: "Empresa",
          links: [
            { label: "Compañia", page: "company" },
            { label: "Servicios", page: "services" },
            { label: "Casos reales", page: "cases" },
          ],
        },
        {
          title: "Productos",
          links: [
            { label: "EasyCounting", href: "https://easycounting.getupsoft.com" },
            { label: "Admin", href: "https://admin.getupsoft.com.do/login" },
            { label: "Cliente", href: "https://cliente.getupsoft.com.do/login" },
          ],
        },
        {
          title: "Contacto",
          links: [
            { label: "ventas@getupsoft.com", href: "mailto:ventas@getupsoft.com" },
            { label: "info@getupsoft.com", href: "mailto:info@getupsoft.com" },
            { label: "Diagnostico inicial", page: "diagnostic" },
          ],
        },
      ],
    },
  },
  en: {
    localeName: "EN",
    switchLabel: "Español",
    ui: {
      languageSuggestion: "Prefer English content for this site?",
      languageSuggestionAction: "Switch to English",
      headerTagline: "Digital transformation, implementation, and operations",
      homeProductsCta: "View products",
      companyPrinciplesLabel: "Principles",
      productsPrimaryCta: "View EasyCounting",
      productIncludesLabel: "Included",
      productAudienceLabel: "Who it is for",
      productOutcomesLabel: "Expected outcome",
      productNextStepLabel: "Next step",
      productNextStepTitle: "Explore the product or schedule an implementation conversation.",
      productPortalClientLabel: "Open client portal",
      productPortalAdminLabel: "Open admin portal",
      productDiagnosticCta: "Book a diagnostic",
      serviceViewDetailLabel: "View service",
      serviceCapabilitiesLabel: "Capabilities",
      serviceOutcomesLabel: "Outcome",
      serviceIdealForLabel: "Ideal for",
      casesChallengeLabel: "Challenge",
      casesInterventionLabel: "Intervention",
      casesReadMoreLabel: "View full case study",
      caseContextLabel: "Context / problem",
      caseEvidenceLabel: "Current evidence",
      caseInterventionDetailLabel: "GetUpSoft intervention",
      caseOutcomeLabel: "Delivered transformation",
      contactChannelsLabel: "Channels",
      contactJourneyLabel: "How to start",
      contactOpenLabel: "Open",
      diagnosticIncludesLabel: "Included",
      diagnosticQuestionsLabel: "Key questions",
      diagnosticCtaLabel: "CTA",
      diagnosticCtaDescription:
        "Use this path to start a conversation around architecture, priorities, and real delivery capacity.",
      diagnosticCtaButton: "Email sales",
    },
    navigation: [
      { page: "home", label: "Home" },
      { page: "company", label: "Company" },
      { page: "services", label: "Services" },
      { page: "solutions", label: "Solutions" },
      { page: "products", label: "Products" },
      { page: "cases", label: "Case studies" },
      { page: "insights", label: "Insights" },
      { page: "contact", label: "Contact" },
      { page: "diagnostic", label: "Diagnostic" },
    ],
    meta: {
      home: {
        title: "GetUpSoft | Digital transformation, implementation and operations",
        description:
          "GetUpSoft helps companies with digital transformation, implementation, integration, operational support, and products such as EasyCounting.",
      },
      company: {
        title: "Company | GetUpSoft",
        description:
          "Learn how GetUpSoft operates as a technology, implementation, integration, and digital transformation company.",
      },
      services: {
        title: "Services | GetUpSoft",
        description:
          "Consulting, implementation, automation, integrations, support, and custom digital solutions for companies.",
      },
      consulting: {
        title: "Digital transformation consulting | GetUpSoft",
        description: "Executive and operational consulting to prioritize architecture, processes, and digital transformation roadmap.",
      },
      implementation: {
        title: "Technology implementation | GetUpSoft",
        description: "Phased implementation of platforms, portals, and digital workflows with operational handover.",
      },
      integrations: {
        title: "Integrations and automation | GetUpSoft",
        description: "Integrations across ERP, product, email, documents, and internal processes to remove friction.",
      },
      digitalization: {
        title: "Corporate digitalization | GetUpSoft",
        description: "Digital rebranding, web experiences, and commercial capture journeys aligned with real operations.",
      },
      solutions: {
        title: "Solutions | GetUpSoft",
        description:
          "Digital solutions for operations, finance, customer experience, integrations, and scalable execution.",
      },
      products: {
        title: "Products | GetUpSoft",
        description:
          "Explore EasyCounting and the productized assets GetUpSoft uses to accelerate implementation work.",
      },
      productDetail: {
        title: "EasyCounting | A GetUpSoft product",
        description:
          "EasyCounting is GetUpSoft's flagship product for fiscal, operational, and accounting control with implementation support.",
      },
      cases: {
        title: "Case studies | GetUpSoft",
        description:
          "Review real client work delivered by GetUpSoft for companies such as Galante's Jewelry and Chefalitas.",
      },
      caseGalantes: {
        title: "Case study: Galante's Jewelry | GetUpSoft",
        description:
          "A real premium rebranding, digital experience, and operational integration project for Galante's Jewelry.",
      },
      caseChefalitas: {
        title: "Case study: Chefalitas | GetUpSoft",
        description:
          "A real digitalization, commercial structure, and website implementation case for Chefalitas.",
      },
      insights: {
        title: "Insights | GetUpSoft",
        description:
          "Thoughtful content about digital transformation, implementation, integrations, and running technology in real businesses.",
      },
      contact: {
        title: "Contact | GetUpSoft",
        description:
          "Talk to GetUpSoft about digital transformation, implementation, support, or product adoption.",
      },
      diagnostic: {
        title: "Initial diagnostic | GetUpSoft",
        description:
          "Book a diagnostic session to define priorities, risks, architecture, and a realistic transformation roadmap.",
      },
    },
    hero: {
      eyebrow: "Consulting, implementation, and digital products",
      title: "We turn digital strategy into systems, operations, and measurable execution.",
      description:
        "GetUpSoft helps companies digitalize, integrate, automate, support, and operate technology. EasyCounting is part of the portfolio, not the whole company.",
      primaryCta: "Book a diagnostic",
      secondaryCta: "See real work",
    },
    homeStats: [
      { label: "Model", value: "Services + implementation + operations + products" },
      { label: "Execution", value: "Rebranding, digitalization, integrations, and delivery" },
      { label: "Proof", value: "Real client projects already live in production" },
    ],
    homeTrust: [
      "Digital transformation consulting",
      "Technology implementation",
      "Odoo / DGII integrations",
      "Post-launch operational support",
    ],
    company: {
      eyebrow: "Company",
      title: "A technology company built for real execution.",
      description:
        "We do not just sell software. We diagnose, guide, implement, integrate, and operate solutions so transformation becomes a sustainable operating model.",
      pillars: [
        {
          title: "Strategic guidance",
          description:
            "We translate business objectives into priorities, architecture, roadmap, and practical technology decisions.",
        },
        {
          title: "Implementation with ownership",
          description:
            "We design and build the solution, connect the tools, and leave the client with a workable operating capability.",
        },
        {
          title: "Ongoing operations",
          description:
            "We stay involved after launch with support, observability, stabilization, and evolution.",
        },
      ],
      principles: [
        "Strategy without execution does not transform operations.",
        "Owned products accelerate delivery but do not replace consulting judgment.",
        "Every implementation should be measurable, operable, and maintainable.",
      ],
    },
    services: {
      eyebrow: "Services",
      title: "Capabilities that run from definition to operations.",
      description:
        "The offer must clearly separate consulting, implementation, integration, and support while still feeling like one company.",
      items: [
        {
          title: "Digital transformation consulting",
          summary: "Process, stack, and operating model assessment to identify what should change first.",
          bullets: ["Current-state diagnostic", "Prioritized roadmap", "Target architecture guidance"],
          page: "consulting",
        },
        {
          title: "Technology implementation",
          summary: "Hands-on rollout of platforms, portals, integrations, and business workflows.",
          bullets: ["Configuration and rollout", "Phased launch", "Operational handover"],
          page: "implementation",
        },
        {
          title: "Integrations and automation",
          summary: "Connecting ERPs, operational tools, communications, and internal processes.",
          bullets: ["Odoo / DGII", "Workflow automation", "System-to-system synchronization"],
          page: "integrations",
        },
        {
          title: "Commercial digitalization",
          summary: "Digital experiences, web presence, and conversion flows connected to business operations.",
          bullets: ["Corporate sites", "Digital rebranding", "Lead capture and activation"],
          page: "digitalization",
        },
        {
          title: "Support and operations",
          summary: "Post-launch support, monitoring, stabilization, and continuous improvement.",
          bullets: ["Runbooks", "Functional support", "Operational continuity"],
        },
      ],
    },
    serviceDetails: {
      consulting: {
        eyebrow: "Consulting",
        title: "Digital transformation consulting with business and architecture judgment.",
        description:
          "We start by structuring the problem: processes, current stack, constraints, ownership, roadmap, and implementation risks.",
        capabilities: [
          "Executive and operational discovery.",
          "Process, system, and friction mapping.",
          "Target architecture and phased priorities.",
        ],
        outcomes: [
          "Better prioritization and decision-making.",
          "Less implementation rework.",
          "A roadmap usable by both business and technology teams.",
        ],
        idealFor: [
          "Companies that are not sure where to start.",
          "Organizations with fragmented tools and low visibility.",
          "Teams that need leadership alignment before execution.",
        ],
        cta: "Request consulting",
      },
      implementation: {
        eyebrow: "Implementation",
        title: "Technology implementation with ownership and real operational rollout.",
        description:
          "We do more than configure software: we launch workflows, connect systems, and leave the team with an operating capability.",
        capabilities: [
          "Phased rollout with concrete deliverables.",
          "Product, portal, and workflow setup.",
          "Operational transfer and post-launch stabilization.",
        ],
        outcomes: [
          "Faster time to operation.",
          "Lower dependency on the vendor for routine execution.",
          "Stronger internal adoption.",
        ],
        idealFor: [
          "Companies that already chose the direction and need execution.",
          "Teams that require product plus integration plus support.",
          "Projects that cannot stop at demo or pilot stage.",
        ],
        cta: "Start implementation",
      },
      integrations: {
        eyebrow: "Integrations",
        title: "Integrations and automation to connect product, ERP, and operations.",
        description:
          "We design bridges between platforms, ERPs, email, documents, and internal workflows to reduce operational friction.",
        capabilities: [
          "Integrations with Odoo, DGII, and internal tools.",
          "Automation for repetitive tasks and support workflows.",
          "Synchronization across systems and channels.",
        ],
        outcomes: [
          "Less duplicate work.",
          "Better cross-functional traceability.",
          "Faster, more auditable processes.",
        ],
        idealFor: [
          "Teams with silos between commercial, finance, and operations.",
          "Companies already using ERP platforms and needing complementary layers.",
          "Operations still relying on frequent manual steps.",
        ],
        cta: "Assess integrations",
      },
      digitalization: {
        eyebrow: "Digitalization",
        title: "Commercial and corporate digitalization to present, capture, and operate better.",
        description:
          "We combine brand, digital experience, and operating structure so the online presence supports real commercial execution.",
        capabilities: [
          "Corporate websites and branded digital experiences.",
          "Digital rebranding and commercial content structuring.",
          "Forms, lead capture, and journeys connected to operations.",
        ],
        outcomes: [
          "Stronger corporate positioning.",
          "More clarity when selling services and products.",
          "A digital foundation aligned with real operations.",
        ],
        idealFor: [
          "Companies that grew without a strong corporate narrative.",
          "Brands moving from basic presence to a real commercial channel.",
          "Businesses that need to sell services, products, or both more effectively.",
        ],
        cta: "Explore digitalization",
      },
    },
    leadForm: {
      eyebrow: "Form",
      title: "Tell us about your context.",
      description: "Use this form to start a diagnostic, implementation conversation, or a more precise commercial discovery.",
      fields: {
        name: "Name",
        company: "Company",
        email: "Email",
        interest: "Primary interest",
        market: "Market / context",
        challenge: "What you need to solve",
      },
      placeholders: {
        name: "Your name",
        company: "Company name",
        email: "you@company.com",
        challenge: "Describe the process, problem, or initiative you need to solve.",
      },
      interests: [
        "Digital transformation consulting",
        "Technology implementation",
        "Integrations and automation",
        "Corporate digitalization",
        "EasyCounting product",
      ],
      markets: ["Dominican Republic", "Latin America", "Regional operation", "Other market"],
      submit: "Send by email",
    },
    solutions: {
      eyebrow: "Solutions",
      title: "Technology organized around business outcomes.",
      description:
        "The company should sell results: control, visibility, integration, and scalable execution.",
      segments: [
        {
          title: "Fiscal and accounting operations",
          summary: "Capabilities for compliance, traceability, and administrative control.",
          bullets: ["E-invoicing workflows", "Accounting synchronization", "Document visibility"],
        },
        {
          title: "Commercial digitalization",
          summary: "Brand presence, web experiences, and commercial journeys connected to operations.",
          bullets: ["Digital rebranding", "Corporate sites", "Lead capture and conversion flows"],
        },
        {
          title: "Enterprise integration",
          summary: "Bridges between products, ERPs, automation, and internal operational tools.",
          bullets: ["Catalog sync", "Channel integration", "Back-office automation"],
        },
      ],
    },
    products: {
      eyebrow: "Products",
      title: "Owned products and reusable assets that accelerate delivery.",
      description:
        "EasyCounting is the flagship product. Around it, GetUpSoft provides reusable assets and consulting-led implementation.",
      items: [
        {
          title: "EasyCounting",
          type: "Owned product",
          summary: "A platform for fiscal, operational, and accounting control with multi-tenant structure and integrations.",
          bullets: ["Issuance and tracking", "Role-based portals", "Governance and integration readiness"],
        },
        {
          title: "Implementation accelerators",
          type: "Productized assets",
          summary: "Components, processes, and playbooks that reduce time to value.",
          bullets: ["Operational templates", "Baseline integrations", "Deployment and observability layers"],
        },
        {
          title: "Custom delivery",
          type: "Service backed by reusable assets",
          summary: "We extend products and build custom modules when the business requires more than a fixed product.",
          bullets: ["Private portals", "Custom workflows", "Automation layers"],
        },
      ],
    },
    productDetail: {
      eyebrow: "Featured product",
      title: "EasyCounting: owned software backed by implementation and operational support.",
      description:
        "EasyCounting should be positioned as a strong product inside a broader consulting and delivery company.",
      includes: [
        "Portals for administration, clients, and partners.",
        "Fiscal, document, and accounting control in one operating base.",
        "Integration paths with Odoo and compliance workflows.",
      ],
      audiences: [
        "Companies that need better administrative control and traceability.",
        "Operational firms that require multi-entity structure and role separation.",
        "Teams that need product plus implementation plus support.",
      ],
      outcomes: [
        "Less day-to-day operational friction.",
        "Better compliance visibility and evidence handling.",
        "A platform ready to grow through integrations and new modules.",
      ],
    },
    cases: {
      eyebrow: "Real work",
      title: "Client projects delivered in production.",
      description:
        "Galante's Jewelry and Chefalitas are not inspiration boards. They are proof of execution in branding, digitalization, and implementation.",
      items: casesEn,
    },
    insights: {
      eyebrow: "Insights",
      title: "Content that sells judgment, not just tools.",
      description:
        "The corporate site should grow with localized content that positions GetUpSoft on transformation, implementation, and operations.",
      pillars: [
        { title: "Applied digital transformation", summary: "Roadmaps, prioritization, and architecture decisions with business impact." },
        { title: "Implementation and integrations", summary: "Lessons from real rollouts, adoption, and operational handoffs." },
        { title: "Products and operations", summary: "How owned software supports process, support, and growth." },
      ],
    },
    contact: {
      eyebrow: "Contact",
      title: "Let's talk about transformation, implementation, or product adoption.",
      description:
        "The contact path should support product demos as well as consulting, integration, and execution opportunities.",
      channels: [
        { label: "ventas@getupsoft.com", description: "Commercial opportunities and diagnostics", href: "mailto:ventas@getupsoft.com" },
        { label: "info@getupsoft.com", description: "General contact and partnerships", href: "mailto:info@getupsoft.com" },
        { label: "EasyCounting", description: "Explore the product", href: "https://easycounting.getupsoft.com" },
      ],
      journeys: [
        { title: "Product demo", description: "For teams already evaluating EasyCounting." },
        { title: "Initial diagnostic", description: "For companies that need to define the problem, architecture, and priorities first." },
        { title: "Implementation / integrations", description: "For projects where the product is only one part of the solution." },
      ],
    },
    diagnostic: {
      eyebrow: "Initial diagnostic",
      title: "A first conversation to structure the problem before building anything.",
      description:
        "The best commercial entry point is a guided diagnostic: current state, constraints, systems, risks, and the operating target.",
      includes: [
        "Discovery session with business and operations focus.",
        "Current systems, process, and friction mapping.",
        "Initial solution hypothesis, risks, and next-step recommendation.",
      ],
      checkpoints: [
        "What process needs to be digitalized or stabilized.",
        "Which systems already exist and which must be integrated.",
        "What outcomes are needed in the next 30, 60, and 90 days.",
      ],
    },
    footer: {
      description:
        "GetUpSoft combines consulting, implementation, integration, operations, and owned products to execute digital transformation with corporate discipline.",
      columns: [
        {
          title: "Company",
          links: [
            { label: "Company", page: "company" },
            { label: "Services", page: "services" },
            { label: "Case studies", page: "cases" },
          ],
        },
        {
          title: "Products",
          links: [
            { label: "EasyCounting", href: "https://easycounting.getupsoft.com" },
            { label: "Admin", href: "https://admin.getupsoft.com.do/login" },
            { label: "Client", href: "https://cliente.getupsoft.com.do/login" },
          ],
        },
        {
          title: "Contact",
          links: [
            { label: "ventas@getupsoft.com", href: "mailto:ventas@getupsoft.com" },
            { label: "info@getupsoft.com", href: "mailto:info@getupsoft.com" },
            { label: "Initial diagnostic", page: "diagnostic" },
          ],
        },
      ],
    },
  },
};
