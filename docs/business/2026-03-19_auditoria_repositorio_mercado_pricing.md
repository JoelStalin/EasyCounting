# 1. Resumen ejecutivo

El repositorio implementa una plataforma SaaS B2B multi-tenant para facturacion electronica y gestion operativa asociada al ecosistema e-CF de Republica Dominicana. La evidencia del codigo confirma un backend FastAPI, cuatro portales React/Vite (`admin`, `cliente`, `socios`, `corporativo`), modelos de planes y consumo, integracion DGII, API empresarial para Odoo, localizacion Odoo 15/19, chatbot tenant-scoped, login social, tours guiados, facturas recurrentes y servicio SMTP.

La oportunidad comercial es real: el producto ya cubre el nucleo transaccional, la operacion multiempresa, el canal de socios y una ruta clara a clientes empresariales con Odoo. El encaje natural de mercado es `tax-tech + e-invoicing + compliance SaaS + managed services` para mipymes, firmas contables, grupos empresariales y proveedores de servicios de facturacion electronica.

Conclusion ejecutiva:

- `Confirmado por el codigo`: el proyecto ya es vendible como SaaS gestionado en entorno controlado para clientes dominicanos que requieren e-CF, portal cliente y operacion multiempresa.
- `Inferido con alta confianza`: la mejor estrategia comercial es venderlo como plataforma principal + servicios profesionales + add-ons premium, no como producto horizontal de bajo costo puro.
- `Hipotesis comercial que debe validarse`: la marca final del producto puede independizarse parcialmente de `GetUpsoft`, pero el empaquetado y pricing ya pueden operar sin esperar ese rebrand.

Listo para venderse hoy: `parcialmente listo`.

Bloqueos reales para venta a escala:

- falta cierre operativo del edge publico estable
- falta bridge runtime vivo con Odoo
- falta cerrar la certificacion DGII real `PRECERT/CERT/PROD`
- falta endurecer billing comercial mas alla del modelo actual de documentos/uso

# 2. Alcance y metodologia

## Alcance auditado

Se revisaron estas superficies del repositorio:

- backend `app/`
- frontend `frontend/apps/*` y `frontend/packages/*`
- Odoo `integration/odoo/`
- despliegue `deploy/`, `docker-compose*.yml`, `ops/`
- pruebas `tests/`, `e2e/`
- documentacion operativa y contexto previo en `docs/` y `.ai_context/`

## Metodologia aplicada

1. Auditoria de repositorio
   - lectura de `README.md`, `pyproject.toml`, `app/main.py`, settings, modelos, routers, servicios, tests y docs ya generadas
2. Mapeo funcional
   - traduccion de rutas, modelos y portales a capacidades de negocio
3. Benchmark de mercado
   - navegacion publica con Selenium
   - contraste con fuentes web directas actuales
4. Sintesis multi-enfoque
   - Enfoque 1: auditor tecnico
   - Enfoque 2: product manager / arquitectura de oferta
   - Enfoque 3: pricing y benchmark competitivo
   - Enfoque 4: riesgos, brechas y readiness comercial

## Uso de Selenium

Se ejecuto una captura navegada de mercado sobre competidores y paginas comerciales publicas. Artefactos:

- `artifacts_live_dns/market_selenium_20260319/results.json`
- `artifacts_live_dns/market_selenium_20260319/01_Alegra_RD_precios.png`
- `artifacts_live_dns/market_selenium_20260319/02_Factoa_RD.png`
- `artifacts_live_dns/market_selenium_20260319/03_DigitalHorizon.png`
- `artifacts_live_dns/market_selenium_20260319/04_Digimart.png`

## Regla de evidencia

- `Confirmado por el codigo`: visible en codigo fuente, tests o artefactos runtime del repo
- `Inferido con alta confianza`: no esta completo en una sola pieza, pero la arquitectura lo respalda
- `Hipotesis razonable`: propuesta comercial o de empaquetado aun no totalmente materializada

# 3. Auditoria tecnica del repositorio

## Arquitectura general

`Confirmado por el codigo`.

El repositorio es un monorepo modular con estas capas:

- FastAPI como backend principal
- PostgreSQL + SQLAlchemy + Alembic
- Redis para primitives/rate limit/jobs
- React/Vite/Tailwind para portales
- Docker Compose y overlays Kubernetes
- integraciones DGII
- addons Odoo 15/19

## Tecnologias detectadas

Backend:

- Python 3.11-3.12
- FastAPI
- SQLAlchemy 2
- Alembic
- Redis
- structlog
- signxml
- reportlab
- httpx
- pydantic-settings

Frontend:

- React 18
- Vite
- Tailwind
- Zustand
- React Query
- `react-joyride` via `frontend/packages/ui/src/guided-tour.tsx`

Infraestructura:

- Docker
- Docker Compose
- Kubernetes manifests
- Nginx
- Prometheus instrumentation
- Sentry opcional
- Cloudflare Tunnel en operacion de borde

## Modulos y flujos clave

### Backend confirmado

- auth portal y MFA: `app/api/routes/auth.py`
- admin portal service: `app/application/admin_portal.py`
- client portal service: `app/application/client_portal.py`
- seller/partner portal: `app/application/partner_portal.py`
- chatbot tenant-scoped: `app/application/tenant_chat.py`
- facturas recurrentes: `app/application/recurring_invoices.py`
- API empresarial Odoo / tenant API: `app/application/tenant_api.py`
- social auth: `app/services/social_auth.py`
- email SMTP: `app/services/email_service.py`
- billing por uso y limites: `app/billing/services.py`
- renderer de representacion impresa: `app/ri/router.py`
- DGII compat y rutas ENFC: `app/api/enfc_routes.py`, `app/api/routes/dgii.py`, `app/dgii/client.py`

### Frontend confirmado

- `admin-portal`: companias, planes, agentes IA, auditoria, usuarios
- `client-portal`: dashboard, comprobantes, planes, asistente, e-CF, RFCE, aprobaciones, certificados, recurrentes, API Odoo, perfil
- `seller-portal`: dashboard, clientes asignados, comprobantes, emision demo, perfil
- `corporate-portal`: sitio comercial con `Accounting Management`

### Odoo confirmado

- baseline Odoo 15: `integration/odoo/odoo15_getupsoft_do_localization`
- baseline Odoo 19: `integration/odoo/odoo19_getupsoft_do_localization`
- laboratorio Odoo 19 activo: `labs/odoo19_chefalitas/docker-compose.yml`

## Hallazgos criticos

1. `Confirmado por el codigo`: el producto ya tiene capas diferenciadas por rol y canal, lo que facilita pricing segmentado.
2. `Confirmado por el codigo`: existe billing base por plan y uso, pero aun no es un motor de monetizacion completamente enterprise.
3. `Confirmado por el codigo`: la integracion Odoo ya tiene dos rutas vendibles.
   - addon/localizacion
   - API empresarial por tenant
4. `Confirmado por el codigo`: la plataforma tiene features premium claras.
   - partner portal
   - API access
   - IA
   - recurrentes
   - Odoo
5. `Confirmado por el runtime/documentacion`: el borde publico todavia no esta completamente endurecido como servicio estable.

# 4. Inventario de servicios y capacidades

| Servicio / capacidad | Descripcion de negocio | Evidencia tecnica | Tipo | Estado de validacion | Potencial comercial | Observaciones |
| --- | --- | --- | --- | --- | --- | --- |
| Emision y recepcion e-CF | Gestiona envio, estado y persistencia de comprobantes | `app/dgii/client.py`, `app/application/ecf_submission.py`, `app/api/enfc_routes.py` | Core | Confirmado por el codigo | Muy alto | Producto principal |
| Representacion impresa (RI) | Genera salida usable de comprobantes | `app/ri/router.py`, `app/ri/render.py`, `tests/test_ri_router.py` | Core | Confirmado por el codigo | Alto | Valioso para operacion y cumplimiento |
| Portal admin | Administra tenants, planes, auditoria, usuarios y AI providers | `frontend/apps/admin-portal`, `app/routers/admin.py` | Core | Confirmado por el codigo | Muy alto | Control de plataforma y managed service |
| Portal cliente | Operacion diaria del emisor empresarial | `frontend/apps/client-portal`, `app/routers/cliente.py` | Core | Confirmado por el codigo | Muy alto | Base SaaS recurrente |
| Portal socios / seller | Canal de revendedores y operadores comerciales | `frontend/apps/seller-portal`, `app/routers/partner.py`, `tests/test_partner_portal.py` | Premium / canal | Confirmado por el codigo | Muy alto | Diferenciador comercial fuerte |
| API empresarial Odoo | Permite a clientes empresariales crear tokens y operar facturas por API | `app/routers/tenant_api.py`, `app/application/tenant_api.py`, `docs/guide/20-odoo-api-cliente-empresarial.md` | Premium | Confirmado por el codigo | Muy alto | Clave para ERP/automatizacion |
| Localizacion Odoo 15/19 | Addons fiscales y de reportes para Odoo | `integration/odoo/odoo15_getupsoft_do_localization`, `integration/odoo/odoo19_getupsoft_do_localization` | Servicio / integracion | Confirmado por el codigo | Muy alto | Puerta clara a proyectos de implementacion |
| Facturas recurrentes | Programa facturas diarias, quincenales, mensuales o personalizadas | `app/application/recurring_invoices.py`, `tests/test_recurring_invoices.py` | Premium | Confirmado por el codigo | Alto | Ya gateado a plan Pro+ |
| Chatbot tenant-scoped | Responde preguntas sobre facturas del tenant | `app/application/tenant_chat.py`, `tests/test_client_chat.py` | Premium | Confirmado por el codigo | Medio-Alto | Debe venderse como eficiencia, no como sustituto de soporte fiscal |
| Agentes IA cloud | Administra proveedores tipo OpenAI/Gemini | `app/routers/admin.py`, `frontend/apps/admin-portal/src/pages/AIProviders.tsx` | Premium | Confirmado por el codigo | Medio | Mas fuerte como add-on enterprise |
| Login social + MFA | Acelera adopcion y endurece acceso | `app/services/social_auth.py`, `tests/test_auth_social_and_tours.py` | Core | Confirmado por el codigo | Medio | Reduce friccion comercial |
| Tours autoguiados | Onboarding guiado por vista | `app/routers/ui_tours.py`, `frontend/*/tours` | Core diferenciador | Confirmado por el codigo | Medio | Mejora activacion y soporte |
| SMTP reusable | Correo operativo y notificaciones | `app/services/email_service.py`, `tests/test_email_service.py` | Add-on / soporte | Confirmado por el codigo | Medio | Aun falta validar deliverability real |
| Ambiente demo independiente | Demo comercial separada con credenciales y seed | `deploy/docker-compose.demo.yml`, `scripts/automation/setup_demo_environment.py` | Comercial | Confirmado por el codigo | Alto | Excelente activo de ventas |
| Sitio corporativo | Portal comercial y de demanda | `frontend/apps/corporate-portal` | Comercial | Confirmado por el codigo | Medio-Alto | Debe pasar al edge publico estable |
| Billing por uso y limites | Soporta limites por plan y cargo por documento | `app/models/billing.py`, `app/billing/services.py` | Core monetizacion | Confirmado por el codigo | Muy alto | Hoy es baseline, no billing completo |
| Publicacion de reportes DGII desde Odoo | Reportes 606/607/608/609 y publicacion guiada | addons Odoo + docs previas | Integracion premium | Inferido con alta confianza | Alto | Aun no cerrada end-to-end |
| White-label | Rebranding profundo del producto | No hay evidencia fuerte actual | Comercial | Hipotesis razonable | Medio | Reservar para enterprise futuro |

# 5. Interpretacion del negocio

## Problema que resuelve

El sistema reduce el costo operativo y el riesgo de cumplimiento de empresas que deben emitir e-CF, controlar sus comprobantes, responder a DGII, operar certificados, generar representacion impresa y conectar ERP/portales sin construir la infraestructura fiscal desde cero.

## Cliente objetivo

### Confirmado por el codigo

- empresas emisoras de e-CF
- tenants corporativos
- administradores de plataforma
- partners/revendedores
- operadores Odoo

### Inferido con alta confianza

- firmas contables y BPO financiero
- integradores ERP
- grupos empresariales multiempresa
- PSFE o emisor principal con canal de distribuidores

## Propuesta de valor emergente

1. Cumplimiento fiscal dominicano con experiencia SaaS moderna
2. Portales diferenciados por rol
3. Ruta de integracion real con Odoo
4. Escalabilidad comercial via partners
5. Automatizacion creciente por capas premium

## Casos de uso mas viables

- pyme que necesita emitir e-CF y tener portal cliente
- empresa mediana con Odoo que quiere conectar comprobantes y reportes
- firma contable que administra multiples clientes
- proveedor/reseller que opera clientes asignados
- empresa que quiere automatizar facturas recurrentes y reporting

## Verticales iniciales recomendadas

- servicios profesionales
- retail ligero y distribuidores
- firmas contables
- cooperativas y negocios con multiempresa
- grupos con operacion administrativa centralizada

# 6. Analisis de mercado

## Categoria de mercado

El proyecto encaja en la interseccion de:

- facturacion electronica / e-invoicing
- tax-tech / compliance SaaS
- ERP connectivity
- managed services para mipymes y medianas empresas

## Tendencias actuales

### Confirmado por fuentes oficiales

- La DGII mantiene activa la presion regulatoria de la Ley 32-23 y continuo impulsando la adopcion de facturacion electronica en 2025.
- La DGII comunica beneficios concretos: reduccion de costos administrativos, automatizacion y seguridad.
- Sigue existiendo `Facturador Gratuito`, lo que fija un piso de mercado en `RD$0` para la emision basica.
- La DGII mantiene la figura de proveedor de servicios y procesos formales de certificacion/autorizacion.

### Implicacion comercial

- competir por precio puro contra el facturador gratuito es mala estrategia
- la monetizacion debe centrarse en automatizacion, integracion, operacion multiempresa, soporte y servicio gestionado

## Tamano y oportunidad de mercado

### Confirmado por fuentes publicas

- MICM reporta que las mipymes representan `98.4%` del total de las empresas formales y generan mas de `879 mil` empleos en RD.
- ONE mantiene un Directorio y Demografia Empresarial Formal 2024, lo que respalda un universo formal grande y segmentable.

### Inferido con alta confianza

El mercado direccionable no es solo "todos los contribuyentes", sino una franja de:

- pymes que necesitan algo mejor que el facturador gratuito
- empresas medianas con ERP o multiusuario
- firmas contables y revendedores
- empresas que valoran integracion Odoo, API y soporte

## Barreras de entrada

- certificacion y cumplimiento DGII
- certificados digitales y operacion segura
- soporte local y conocimiento normativo
- integraciones ERP
- confianza comercial y continuidad operativa

## Sensibilidad al precio

- microempresas: alta
- pymes en crecimiento: media
- medianas / grupos / firmas contables: menor sensibilidad y mas foco en soporte, integracion y riesgo

## Oportunidades de diferenciacion

- seller portal / canal indirecto
- Odoo 15 + Odoo 19
- tenant API empresarial
- tours autoguiados + onboarding
- AI assistant con aislamiento por tenant
- enfoque combinado SaaS + implementacion + managed service

## Riesgos competitivos

- presion del facturador gratuito DGII en el segmento mas bajo
- suites contables consolidadas con pricing simple
- competidores locales con discurso fuerte de certificacion DGII
- erosión de margen si se sobredimensiona el soporte incluido en planes bajos

## Posicionamiento recomendado

`Plataforma dominicana de facturacion electronica y operacion fiscal para empresas que necesitan mas control, mas integracion y menos friccion que un facturador basico.`

# 7. Benchmark competitivo

| Competidor | Segmento | Propuesta | Features comparables | Precio visible | Observaciones | Comparacion con el proyecto |
| --- | --- | --- | --- | --- | --- | --- |
| DGII Facturador Gratuito | Micro y contribuyente de entrada | Emision gratuita conforme a DGII | Emision basica de e-CF | Gratis | Baseline regulatorio; la propia DGII documenta limitaciones y menor integracion con sistemas internos | El proyecto debe diferenciarse por automatizacion, portales, Odoo, API, soporte y multiempresa |
| Alegra RD | Pyme y contabilidad cloud | Contabilidad + factura electronica | Facturacion, usuarios por plan, prueba gratis, producto cloud | `US$29`, `US$59`, `US$89`, `US$129` mensuales en la pagina RD | Packaging muy claro, foco pyme, prueba gratis fuerte | El proyecto tiene mas verticalidad fiscal dominicana y seller portal, pero menos madurez comercial publica |
| DigitalHorizon | Mipyme a enterprise | e-CF certificado con seguridad y AWS | Planes por volumen, calculadora, portal cliente, infraestructura y compliance | Desde `RD$990` hasta `RD$19,900`, mas plan ilimitado cotizado | Mensaje muy alineado a seguridad, certificacion y escalamiento por documentos | El proyecto compite bien en amplitud funcional, pero debe igualar claridad comercial y edge publico estable |
| Factoa RD | Pyme / ERP liviano / POS | Facturacion electronica + inventario + POS + compras | ERP ligero, POS, inventario, mobile, personalizacion | No visible en la landing auditada | Mensaje fuerte de software integral; precios no publicados en la evidencia navegada | El proyecto hoy es mas fuerte en portales diferenciados, API y partner model, pero menos maduro como ERP completo propio |
| Digimart | Negocio dominicano integral | Gestion empresarial completa en la nube | e-CF, POS, inventario, nomina, portal clientes, multiempresa para firmas | No visible en la landing auditada; CTA a demo y cuenta gratis | Empuja all-in-one con lenguaje muy local y verticales especificos | El proyecto es mas fuerte en DGII/Odoo/canal seller; Digimart comunica mejor amplitud operativa inmediata |

## Lectura competitiva

- `Confirmado por el mercado`: los competidores reservan automatizacion, volumen, multiusuario y enterprise features para capas superiores.
- `Inferido con alta confianza`: el proyecto puede competir por especializacion fiscal + integracion Odoo + canal indirecto, no por commodity.
- `Hipotesis razonable`: el nicho mas rentable inicial es `pyme en crecimiento + firma contable + integrador Odoo`, no microemisor puro.

# 8. Propuesta de productos y servicios

## Producto principal

### GetUpsoft e-CF Cloud

Cliente objetivo:

- mipymes y medianas dominicanas obligadas o migrando a e-CF

Beneficio principal:

- emitir, controlar, consultar y operar comprobantes electronicos con cumplimiento y experiencia SaaS

Incluye:

- portal cliente
- emision y consulta e-CF
- RI
- certificados
- dashboard
- control de planes y consumo

No incluye por defecto:

- implementacion ERP profunda
- seller channel
- proyectos enterprise custom

## Productos / add-ons secundarios

### API Empresarial

- acceso API por tenant
- tokens autogestionados
- ideal para ERP, middleware y automatizacion

### Odoo Connector Pack

- addon/localizacion Odoo
- consumo de `tenant-api`
- implementacion y soporte de integracion

### Automation Pack

- facturas recurrentes
- jobs operativos
- reglas de automatizacion futuras

### AI Assist Pack

- chatbot tenant-scoped
- proveedores IA cloud administrados por plataforma

### Partner / Reseller Console

- seller portal
- gestion de clientes asignados
- emision demo / operaciones delegadas

### Managed Compliance Services

- onboarding fiscal
- carga y gestion de certificados
- acompanamiento DGII
- soporte operativo

### Servicios profesionales

- implementacion
- migracion
- capacitacion
- parametrizacion Odoo
- hardening y despliegue

# 9. Planes y tarifas recomendadas

## Principios de pricing

1. No competir con el facturador gratuito en el plan de entrada
2. Monetizar automatizacion e integracion
3. Cobrar implementacion aparte en clientes con Odoo o cumplimiento gestionado
4. Reservar seller/API/automatizacion fuerte para capas superiores

## Arquitectura recomendada

| Plan | Cliente objetivo | Que incluye | Limites sugeridos | Precio mensual | Precio anual | Justificacion | Upsell recomendado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Basico | micro y pyme inicial que quiere salir del facturador gratuito | portal cliente, emision manual, consulta, RI, dashboard, soporte base | 300-500 docs/mes, 1 usuario incluido, sin recurrentes, sin API empresarial | `RD$1,490` | `RD$15,200` | Se ubica arriba de `RD$0` pero por debajo de capas medias locales; cobra conveniencia y operacion | subir a Pro por automatizacion e integracion |
| Profesional | pyme en crecimiento | todo Basico + facturas recurrentes + API Odoo/ERP + mejor operacion | 2,500 docs/mes, 3 usuarios sugeridos, recurrentes incluidas, API incluida | `RD$2,990` | `RD$30,500` | Muy alineado con el valor del codigo actual y con el mercado medio local | subir a Premium por multiempresa/managed |
| Premium | empresa mediana, firma contable o negocio multioperador | todo Pro + soporte prioritario + seller/partner capabilities segun caso + AI assist + onboarding asistido | 5,000 docs/mes, 8 usuarios sugeridos, multiempresa ligero, AI, integraciones asistidas | `RD$5,900` | `RD$60,200` | Posiciona el producto por encima del SaaS pyme basico y antes del enterprise custom | subir a Enterprise por SLA y customizacion |
| Enterprise | grupos empresariales, PSFE, firmas grandes e integradores | todo Premium + SLA, despliegue guiado, gobernanza, volumen alto, integracion Odoo formal, soporte senior | 10,000+ docs/mes, usuarios y tenants acordados, soporte dedicado, SOW | `Desde RD$12,900` + setup | cotizacion anual | Coherente con competidores locales enterprise y con el valor de integracion/servicio | add-ons de managed compliance, white-glove DGII, Odoo enterprise |

## Setup fee recomendado

| Oferta | Setup fee sugerido | Comentario |
| --- | --- | --- |
| Basico | `RD$0 - RD$7,500` | idealmente self-serve o onboarding remoto ligero |
| Profesional | `RD$12,500 - RD$25,000` | para configuracion fiscal y training |
| Premium | `RD$35,000 - RD$75,000` | integracion, soporte inicial y parametrizacion |
| Enterprise | `Desde RD$120,000` | proyecto formal, Odoo, DGII, seguridad y acompanamiento |

## Decisiones de empaquetado

- `Confirmado por el codigo`: `facturas recurrentes` deben quedar en `Pro / Profesional` y no en `Basico`
- `Confirmado por el codigo`: `API Odoo` encaja desde `Pro`
- `Inferido con alta confianza`: seller portal y AI cloud deben reservarse para `Premium+`
- `Hipotesis razonable`: white-label debe vivir solo en `Enterprise`

## Modelo comercial recomendado

- No freemium
- Si `trial guiado` de 14-15 dias
- Demo guiada siempre
- Cobro por organizacion + volumen documental
- Add-ons para implementacion, integraciones y soporte

# 10. Reglas de negocio propuestas

| Categoria | Regla | Objetivo | Impacto ingresos | Impacto costos | Impacto CX | Prioridad | Naturaleza |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Alta | todo cliente entra por demo guiada o trial controlado | filtrar prospectos y activar rapido | Alto | Bajo | Alto | P0 | Obligatoria |
| Onboarding | no se habilita emision real sin onboarding fiscal completo y certificado valido | reducir riesgo fiscal | Medio | Bajo | Medio | P0 | Obligatoria |
| Planes | `Basico` sin recurrentes ni API write | proteger margen y upsell | Alto | Bajo | Medio | P0 | Obligatoria |
| Planes | `Pro` habilita recurrentes y `tenant-api` | monetizar automatizacion | Alto | Bajo | Alto | P0 | Obligatoria |
| Usuarios | limite de usuarios por plan, ampliable por add-on | controlar costo de soporte | Medio | Medio | Medio | P1 | Recomendada |
| Consumo | exceso documental se cobra por bloque o por documento | capturar crecimiento | Alto | Bajo | Medio | P0 | Obligatoria |
| Upgrade | upgrade inmediato; downgrade al siguiente ciclo | facilitar expansion sin perder ingreso | Alto | Bajo | Alto | P0 | Obligatoria |
| Mora | suspender emision nueva tras 7 dias de mora y lectura total tras 30 dias | proteger caja | Alto | Bajo | Medio | P0 | Obligatoria |
| API | tokens por tenant, scopes y expiracion opcional | seguridad y monetizacion de integraciones | Medio | Bajo | Alto | P0 | Obligatoria |
| Soporte | `Basico` best-effort, `Pro` prioridad comercial, `Premium` prioritario, `Enterprise` SLA | alinear promesa y costo | Alto | Alto | Alto | P1 | Obligatoria |
| Add-ons | Odoo, managed compliance, training y seller enablement se cotizan aparte | evitar regalar servicios profesionales | Alto | Medio | Medio | P0 | Obligatoria |
| Seguridad | MFA en admin, logs de auditoria, aislamiento tenant, control de abuse | reducir riesgo reputacional | Medio | Medio | Alto | P0 | Obligatoria |
| Enterprise | cualquier personalizacion fuerte requiere SOW, setup y ventana de cambios | evitar deuda no pagada | Alto | Medio | Medio | P1 | Obligatoria |
| Trial | trial sin certificados productivos ni emision fiscal real | reducir riesgo y costo | Medio | Bajo | Alto | P0 | Obligatoria |
| Reembolso | sin reembolso en setup; suscripcion mensual prorrateada solo por error interno comprobado | proteger margen | Medio | Bajo | Medio | P1 | Recomendable |

# 11. Riesgos y brechas para comercializacion

## Riesgos de producto

- `Confirmado por el runtime`: `cloudflared` sigue como proceso de usuario, no como servicio persistente
- `Confirmado por docs y checklist`: falta publicar `www.getupsoft.com.do` estable extremo a extremo
- `Confirmado por checklist`: bridge runtime con Odoo aun no esta vivo
- `Confirmado por checklist`: certificacion DGII real sigue fuera del cierre tecnico
- `Confirmado por el worktree`: coexistencia `src/*.ts(x)` y `src/*.js` introduce drift en frontend

## Riesgos de monetizacion

- billing actual no implementa todavia seats, cobro anual, trial controlado y dunning real
- soporte incluido puede destruir margen si no se limita por plan
- demasiadas features premium en capas bajas canibalizan `Premium`

## Riesgos competitivos

- precio demasiado bajo frente al costo real de soporte e implementacion
- precio demasiado alto si no se cierra el edge publico y la certificacion real
- discurso comercial debil frente a competidores con pricing publico mas claro

# 12. Recomendaciones estrategicas

1. Lanzar primero `Profesional` como plan ancla.
   - Es el mejor balance entre valor confirmado y ticket defendible.
2. Ir primero a estos segmentos:
   - firmas contables
   - pymes en crecimiento
   - clientes Odoo
   - revendedores/integradores
3. Reservar para `Premium / Enterprise`:
   - seller portal operativo
   - AI cloud gestionada
   - soporte prioritario
   - despliegue gestionado
   - Odoo con acompanamiento
4. No vender todavía:
   - certificacion DGII real automatizada como si ya estuviera cerrada
   - white-label como feature estandar
5. Mejorar antes de salir con agresividad:
   - edge publico estable
   - bridge Odoo vivo
   - pagina de pricing publica clara
   - dunning/comercial billing

# 13. Plan de accion 30 / 60 / 90 dias

## 0-30 dias

- publicar pricing y CTA claros en el corporate portal
- estabilizar edge publico y `www`
- cerrar deliverability SMTP real
- convertir `Profesional` en oferta comercial oficial
- preparar deck de demo y trial guiado

## 31-60 dias

- cerrar bridge Odoo runtime minimo viable
- vender primer paquete `Odoo Connector Pack`
- instrumentar politicas de upgrade/downgrade/mora
- activar reporting comercial por plan, tenant y partner

## 61-90 dias

- cerrar 2-3 implementaciones reales de referencia
- formalizar canal de partners
- empaquetar `Premium` y `Enterprise`
- evaluar rebrand del producto bajo arquitectura respaldada por `GetUpsoft`

# 14. Anexo de evidencias

## Archivos clave revisados

- `README.md`
- `pyproject.toml`
- `app/main.py`
- `app/infra/settings.py`
- `app/models/billing.py`
- `app/models/tenant.py`
- `app/models/user.py`
- `app/models/invoice.py`
- `app/application/client_portal.py`
- `app/application/partner_portal.py`
- `app/application/tenant_chat.py`
- `app/application/tenant_api.py`
- `app/application/recurring_invoices.py`
- `app/services/social_auth.py`
- `app/services/email_service.py`
- `app/routers/admin.py`
- `app/routers/cliente.py`
- `app/routers/partner.py`
- `app/routers/tenant_api.py`
- `frontend/apps/*`
- `integration/odoo/*`
- `deploy/docker-compose.demo.yml`
- `scripts/automation/setup_demo_environment.py`
- `scripts/automation/seed_public_demo_data.py`

## Tests y evidencias internas

- `tests/test_auth_social_and_tours.py`
- `tests/test_partner_portal.py`
- `tests/test_tenant_api_tokens.py`
- `tests/test_recurring_invoices.py`
- `tests/test_client_chat.py`
- `tests/test_email_service.py`
- `.ai_context/test_evidence/2026-03-19_master_plan_validation.md`
- `.ai_context/current_state/2026-03-19_master_plan_runtime_state.md`
- `.ai_context/current_state/2026-03-19_odoo15_getupsoft_lab_and_credentials.md`

## Evidencia Selenium de mercado

- `artifacts_live_dns/market_selenium_20260319/results.json`
- `artifacts_live_dns/market_selenium_20260319/01_Alegra_RD_precios.png`
- `artifacts_live_dns/market_selenium_20260319/02_Factoa_RD.png`
- `artifacts_live_dns/market_selenium_20260319/03_DigitalHorizon.png`
- `artifacts_live_dns/market_selenium_20260319/04_Digimart.png`

## Fuentes externas consultadas

- DGII documentacion e-CF: `https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/documentacionSobreE-CF.aspx`
- DGII FAQ Facturador Gratuito: `https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Preguntas%20frecuentes/Generales/Preguntas-Frecuentes-Facturador-Gratuito.pdf`
- DGII noticia adopcion 2025: `https://dgii.gov.do/noticias/Paginas/Facturacion-Electronica-verdadera-transformacion-nuestra-manera-hacer-negocios.aspx`
- DGII proveedor de servicios e-CF: `https://dgii.gov.do/servicios/Paginas/det-Facturacion-SolicitudProveedorFacturacionElectronica.aspx`
- Proceso certificacion PSFE: `https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Documentacin%20sobre%20eCF/Documentaciones%20Proceso%20de%20Certificaci%C3%B3n%20FE/Proceso%20Certificacion%20para%20ser%20Proveedor%20de%20Servicios%20eCF.pdf`
- Alegra RD pricing: `https://www.alegra.com/rdominicana/contabilidad/precios/`
- Factoa RD: `https://factoa.net/home-rd`
- DigitalHorizon: `https://digitalhorizonrd.com/`
- Digimart: `https://www.digimart.cloud/`
- ONE Directorio empresarial formal 2024: `https://www.one.gob.do/media/sluasbld/directorio-y-demograf%C3%ADa-empresarial-formal-2024x.pdf`
- MICM monitor mipymes: `https://micm.gob.do/direcciones/analisis-economico/el-monitor-de-industria-comercio-y-mipymes/`
- MICM nota mipymes 98.4%: `https://micm.gob.do/viceministro-morales-paulino-ratifica-apoyo-del-micm-a-mipymes/`

## Notas de inferencia e hipotesis

- La oportunidad como PSFE / proveedor gestionado se infiere con alta confianza por el alcance funcional y la documentacion DGII, pero no esta cerrada en produccion.
- La propuesta `Premium` y `Enterprise` es una arquitectura comercial recomendada; no todos sus limites estan codificados hoy.
- El rebrand del producto queda fuera de esta auditoria y sigue como decision estrategica posterior.
