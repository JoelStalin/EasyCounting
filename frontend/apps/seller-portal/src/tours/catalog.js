export const SELLER_TOURS = [
    {
        viewKey: "seller-dashboard",
        patterns: ["/dashboard"],
        version: 1,
        steps: [
            { target: "h1", content: "Este dashboard resume cartera, facturas y estado comercial del partner." },
            { target: "[data-tour='portal-nav']", content: "Desde aqui navegas a clientes, comprobantes y emision demo." },
            { target: "[data-tour='session-user']", content: "La cabecera confirma el partner autenticado." },
        ],
    },
    {
        viewKey: "seller-clients",
        patterns: ["/clients"],
        version: 1,
        steps: [
            { target: "h1", content: "Esta vista lista los clientes asignados al socio actual." },
            { target: "[data-tour='portal-nav']", content: "El menu respeta los permisos del rol reseller, operator o auditor." },
        ],
    },
    {
        viewKey: "seller-invoices",
        patterns: ["/invoices"],
        version: 1,
        steps: [
            { target: "h1", content: "Aqui revisas los comprobantes de la cartera permitida." },
            { target: "[data-tour='session-user']", content: "Siempre valida la sesion antes de operar sobre clientes asignados." },
        ],
    },
    {
        viewKey: "seller-emit",
        patterns: ["/emit/ecf"],
        version: 1,
        steps: [
            { target: "h1", content: "Este flujo genera comprobantes demo solo para tenants asignados." },
            { target: "#tenantId", content: "Selecciona primero el cliente permitido antes de emitir." },
        ],
    },
    {
        viewKey: "seller-profile",
        patterns: ["/profile"],
        version: 1,
        steps: [
            { target: "h1", content: "El perfil del socio resume la cuenta comercial y el rol activo." },
            { target: "[data-tour='tour-trigger']", content: "Puedes relanzar el tour desde el header cuando quieras." },
        ],
    },
];
