export const CLIENT_TOURS = [
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
            { target: "[data-tour='portal-nav']", content: "Desde aqui accedes a facturas, emision, certificados y asistente." },
            { target: "[data-tour='session-user']", content: "Siempre valida la sesion activa antes de emitir o aprobar." },
        ],
    },
    {
        viewKey: "client-invoices",
        patterns: ["/invoices", "/invoices/:id"],
        version: 1,
        steps: [
            { target: "h1", content: "Consulta estados DGII, detalles y consumo de tus comprobantes." },
            { target: "[data-tour='portal-nav']", content: "Puedes saltar a emision o planes sin salir del portal." },
        ],
    },
    {
        viewKey: "client-plans",
        patterns: ["/plans"],
        version: 1,
        steps: [
            { target: "h1", content: "Aqui revisas o solicitas cambios del plan comercial de tu tenant." },
            { target: "[data-tour='tour-trigger']", content: "Usa este boton para repetir el recorrido cuando lo necesites." },
        ],
    },
    {
        viewKey: "client-assistant",
        patterns: ["/assistant"],
        version: 1,
        steps: [
            { target: "h1", content: "El asistente responde solo sobre la informacion del tenant autenticado." },
            { target: "[data-tour='session-user']", content: "La segregacion se aplica por sesion y tenant." },
        ],
    },
    {
        viewKey: "client-emit-ecf",
        patterns: ["/emit/ecf"],
        version: 1,
        steps: [
            { target: "h1", content: "Aqui preparas y envias el XML firmado del e-CF." },
            { target: "textarea", content: "Carga el payload firmado antes de ejecutar el envio." },
        ],
    },
    {
        viewKey: "client-recurring-invoices",
        patterns: ["/recurring-invoices"],
        version: 1,
        steps: [
            { target: "h1", content: "Aqui programas facturas diarias, quincenales, mensuales o personalizadas." },
            { target: "[data-tour='recurring-form']", content: "Define la plantilla, el tipo e-CF y el rango de ejecucion." },
            { target: "[data-tour='recurring-run-due']", content: "Este boton permite procesar manualmente las programaciones vencidas." },
            { target: "[data-tour='recurring-list']", content: "Revisa el historial corto y pausa o reanuda cada programacion." },
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
