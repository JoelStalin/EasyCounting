import type { GuidedTourStep } from "@getupsoft/ui";

export interface ViewTourDefinition {
  viewKey: string;
  patterns: string[];
  version: number;
  steps: GuidedTourStep[];
}

export const CLIENT_TOURS: ViewTourDefinition[] = [
  {
    viewKey: "client-onboarding",
    patterns: ["/onboarding"],
    version: 1,
    steps: [
      { target: "h1", content: "Completa este setup para habilitar tu tenant con datos fiscales correctos." },
      { target: "[data-tour='portal-nav']", content: "El menu queda disponible, pero el flujo operativo se libera al completar el onboarding." },
    ],
  },
  {
    viewKey: "client-dashboard",
    patterns: ["/dashboard"],
    version: 1,
    steps: [
      { target: "h1", content: "Este dashboard muestra el estado operativo de tu cuenta cliente." },
      { target: "[data-tour='portal-nav']", content: "Desde aquí accedes a facturas, emisión, certificados y el asistente." },
      { target: "[data-tour='session-user']", content: "Siempre valida tu sesión activa antes de emitir o aprobar." },
    ],
  },
  {
    viewKey: "client-invoices",
    patterns: ["/invoices", "/invoices/:id"],
    version: 1,
    steps: [
      { target: "h1", content: "Consulta estados de la DGII, detalles y consumo de tus comprobantes." },
      { target: "[data-tour='portal-nav']", content: "Puedes saltar a emisión o revisar planes sin salir del portal." },
    ],
  },
  {
    viewKey: "client-plans",
    patterns: ["/plans"],
    version: 1,
    steps: [
      { target: "h1", content: "Aquí revisas o solicitas cambios del plan comercial de tu tenant." },
      { target: "[data-tour='tour-trigger']", content: "Usa este botón para repetir el recorrido cuando lo necesites." },
    ],
  },
  {
    viewKey: "client-assistant",
    patterns: ["/assistant"],
    version: 1,
    steps: [
      { target: "h1", content: "El asistente responde exclusivamente sobre la información de la empresa (tenant) activa." },
      { target: "[data-tour='session-user']", content: "La segregacion se aplica por sesion y tenant." },
    ],
  },
  {
    viewKey: "client-emit-ecf",
    patterns: ["/emit/ecf"],
    version: 2,
    steps: [
      { 
        target: "h1", 
        content: "🎓 ¡Bienvenido al Tutor Automático Interactivo! Aquí aprenderás cómo emitir y parametrizar correctamente un Comprobante Fiscal Electrónico (e-CF)." 
      },
      { 
        target: "#tour-step-tipo-ecf", 
        content: "📋 **Tipo de e-CF (Obligatorio)**\nDefine la naturaleza fiscal del comprobante.\n• Ej: '31' para B2B que requiere ITBIS, o '32' para B2C final.\n🔴 Si el cliente no tiene RNC, no puedes elegir '31'." 
      },
      { 
        target: "#tour-step-rnc", 
        content: "🏢 **RNC o Cédula (Obligatorio/Condicional)**\nEl número de identificación tributaria del comprador. Debe validar estructura matemática DGII (9 u 11 dígitos).\n💡 *Recomendación:* Si emites un tipo '32' (Consumo) y el monto > RD$250,000, la cédula se vuelve obligatoria." 
      },
      { 
        target: "#tour-step-monto", 
        content: "💰 **Cobro Total (Obligatorio)**\nMonto final a facturar incluyendo impuestos.\n⚙️ *Impacto:* Determina los umbrales de alerta y posibles cruces de validación fiscal por montos altos." 
      },
      { 
        target: "#tour-step-itbis", 
        content: "📊 **ITBIS Facturado (Opcional)**\nEl tributo calculado (18% típico). En Certia puedes parametrizarlo para que asuma productos exentos (0%) según el catálogo o lo declare automáticamente." 
      },
      { 
        target: "#tour-step-payload", 
        content: "🧩 **Payload JSON/XML**\nA nivel de API, Certia procesará todos los artículos, ITBIS retenidos y retenciones de ISR. Si hay dependencias estructurales, las explicamos en la validación." 
      },
      { 
        target: "#tour-step-sync", 
        content: "⚡ **Transmisión Ágil (Toggle)**\nValores: [Activado/Desactivado].\n• *Activado (Default):* Transmisión sincronizada inmediata en el botón ('Fire and Forget').\n• *Desactivado:* Envío asincrónico por bacheras nocturnas para grandes flujos comerciales." 
      },
      { 
        target: "#tour-step-submit", 
        content: "✅ **Botón Inteligente de Emisión**\nAl presionar este botón, antes de ir a DGII, Certia detectará ERRORES de captura (Ej.. RNC inventado, montos ilógicos). ¡Si todo está correcto, habrás emitido tu e-CF!" 
      },
    ],
  },
  {
    viewKey: "client-recurring-invoices",
    patterns: ["/recurring-invoices"],
    version: 1,
    steps: [
      { target: "h1", content: "Aquí programas facturas diarias, quincenales, mensuales o personalizadas." },
      { target: "[data-tour='recurring-form']", content: "Define la plantilla, el tipo de e-CF y el rango de ejecución." },
      { target: "[data-tour='recurring-run-due']", content: "Este botón permite procesar manualmente las programaciones vencidas." },
      { target: "[data-tour='recurring-list']", content: "Revisa el historial a corto plazo; puedes pausar o reanudar cada programación." },
    ],
  },
  {
    viewKey: "client-emit-rfce",
    patterns: ["/emit/rfce"],
    version: 1,
    steps: [
      { target: "h1", content: "Este flujo sirve para resumanes RFCE en escenarios permitidos." },
      { target: "textarea", content: "Pega aqui el resumen XML antes de transmitirlo." },
    ],
  },
  {
    viewKey: "client-approvals",
    patterns: ["/approvals"],
    version: 1,
    steps: [
      { target: "h1", content: "Administra respuestas y aprobaciones comerciales ligadas a tus comprobantes." },
      { target: "[data-tour='portal-nav']", content: "El menu lateral te deja volver rapido a certificados o perfil." },
    ],
  },
  {
    viewKey: "client-certificates",
    patterns: ["/certificates"],
    version: 1,
    steps: [
      { target: "h1", content: "Aqui gestionas el certificado digital del tenant." },
      { target: "[data-tour='session-user']", content: "Verifica la cuenta activa antes de subir o rotar certificados." },
    ],
  },
  {
    viewKey: "client-odoo-api",
    patterns: ["/integrations/odoo"],
    version: 1,
    steps: [
      { target: "h1", content: "Esta seccion genera tokens por tenant para integrar Odoo o cualquier ERP empresarial." },
      { target: "[data-tour='api-token-form']", content: "Aqui defines si la integracion solo lee facturas o tambien registra comprobantes." },
      { target: "[data-tour='api-endpoints']", content: "Copia la base URL y los endpoints exactos que debes configurar en Odoo." },
      { target: "[data-tour='api-token-list']", content: "Revoca credenciales viejas sin afectar otros integradores del mismo tenant." },
    ],
  },
  {
    viewKey: "client-profile",
    patterns: ["/profile"],
    version: 1,
    steps: [
      { target: "h1", content: "Tu perfil concentra informacion de acceso y contexto operativo." },
      { target: "[data-tour='session-user']", content: "Esta cabecera refleja siempre el usuario autenticado." },
    ],
  },
];
