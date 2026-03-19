# Long-Term Prompt Memory

Fecha de inicialización: 2026-03-19
Ámbito: memoria persistente del repositorio para registrar prompts del usuario, errores detectados, decisiones y soluciones aplicadas.

## Política de uso

- Este archivo debe actualizarse cuando el usuario emita prompts relevantes de producto, arquitectura, integración, despliegue, cumplimiento, pricing, branding, QA o documentación.
- Cada entrada debe registrar:
  - objetivo del prompt
  - errores, brechas o tensiones detectadas
  - solución implementada o decisión tomada
  - estado actual
  - evidencia o archivos relevantes
- No registrar credenciales, tokens, cookies ni secretos.
- Cuando una tarea sea sensible o legalmente controlada, registrar la restricción operativa y el motivo.

## Memoria consolidada de prompts

### 2026-03-18 a 2026-03-19 - Migración Odoo y localización dominicana

- Prompt/objetivo:
  - migrar y adaptar la localización Odoo dominicana al proyecto `dgii_encf`
  - asegurar compatibilidad con Odoo 19 y mantener una copia funcional para Odoo 15
- Errores o brechas detectadas:
  - nomenclatura inconsistente en `integration/odoo`
  - dependencias legacy y uso de servicios externos en algunos flujos fiscales
  - POS Odoo 19 pendiente de reescritura
- Solución/decisión:
  - se consolidaron árboles versionados por serie Odoo
  - se dejó `odoo15_getupsoft_do_localization` y `odoo19_getupsoft_do_localization`
  - se mantuvo pendiente el rewrite POS OWL para Odoo 19
- Estado:
  - parcialmente resuelto
- Evidencia:
  - `integration/odoo/odoo15_getupsoft_do_localization/`
  - `integration/odoo/odoo19_getupsoft_do_localization/`

### 2026-03-18 - Política de no depender de servicios externos en Odoo

- Prompt/objetivo:
  - eliminar dependencias externas no controladas y construir servicios propios cuando fuera necesario
- Errores o brechas detectadas:
  - búsqueda/autocompletado y validaciones atadas a proveedores externos
  - necesidad de fallback local controlado
- Solución/decisión:
  - se definió directorio local y backend propio como fallback operativo
  - la política base quedó: preferir servicios internos o catálogos locales
- Estado:
  - resuelto a nivel de estrategia y base técnica
- Evidencia:
  - `app/services/`
  - `integration/odoo/*/getupsoft_l10n_do_rnc_search/`

### 2026-03-18 - Autocompletado fiscal por RNC/Cédula

- Prompt/objetivo:
  - usar la consulta oficial DGII para autocompletar partners Odoo por RNC o cédula
- Errores o brechas detectadas:
  - ausencia de un servicio oficial encapsulado dentro del repo
  - necesidad de parsing robusto y fallback controlado
- Solución/decisión:
  - se integró scraping/consulta web oficial y se conectó con el flujo de partner
  - se mantuvo fallback backend/local
- Estado:
  - resuelto funcionalmente
- Evidencia:
  - `integration/odoo/*/services/dgii_rnc_web.py`
  - `tests/test_dgii_rnc_web_parser.py`

### 2026-03-18 - Pruebas funcionales visuales

- Prompt/objetivo:
  - ejecutar pruebas visuales con Selenium y dejar evidencia gráfica
- Errores o brechas detectadas:
  - entorno frontend no siempre compilable
  - necesidad de headed mode, screenshots y reporte HTML
- Solución/decisión:
  - se creó y estabilizó el arnés Selenium con captura visual y reportes
  - se repitieron corridas en Chrome y Edge
- Estado:
  - resuelto para portales locales y demos visuales
- Evidencia:
  - `e2e/artifacts/`
  - `scripts/automation/run_selenium_live.ps1`

### 2026-03-18 - Chatbot tenant-scoped

- Prompt/objetivo:
  - agregar motor LLM para que cada usuario consulte solo sus propias facturas y comprobantes
- Errores o brechas detectadas:
  - riesgo de fuga cross-tenant
  - falta de configuración centralizada de proveedor IA
- Solución/decisión:
  - se implementó chatbot con filtrado estricto por `tenant_id`
  - se bloquearon cuentas `platform_*` para acceso tenant
- Estado:
  - resuelto a nivel base backend/frontend
- Evidencia:
  - `app/application/tenant_chat.py`
  - `tests/test_client_chat.py`

### 2026-03-18 - Administración de proveedores IA cloud

- Prompt/objetivo:
  - permitir que `platform_superroot` configure proveedores IA desde el panel admin
- Errores o brechas detectadas:
  - no existía UI ni modelo persistente para proveedores cloud
  - riesgo de exposición de claves
- Solución/decisión:
  - se agregaron modelos, router y pantalla `Agentes IA`
  - las API keys quedaron enmascaradas en UI
- Estado:
  - resuelto
- Evidencia:
  - `app/models/platform_ai.py`
  - `frontend/apps/admin-portal/src/pages/AIProviders.tsx`

### 2026-03-18 - Certificación DGII y automatización sensible

- Prompt/objetivo:
  - avanzar la certificación/habilitación como emisor y automatizar interacción DGII
- Errores o brechas detectadas:
  - proceso fiscal/legal de alto impacto
  - pasos de firma, declaración y envío no deben ejecutarse automáticamente
  - faltaba certificado `.p12` y evidencia real de `CERT/PROD`
- Solución/decisión:
  - se definió una política estricta: no automatizar acciones sensibles sin confirmación humana explícita
  - la certificación real quedó como proceso asistido y auditado, no ciego
- Estado:
  - bloqueado externamente / asistido
- Evidencia:
  - `docs/`
  - `.ai_context/current_state/`

### 2026-03-18 - Publicación pública, DNS y Cloudflare

- Prompt/objetivo:
  - dejar el proyecto accesible públicamente sin depender de AWS
- Errores o brechas detectadas:
  - DNS inconsistentes
  - túnel Cloudflare con errores operativos intermitentes
  - dependencia de pasos humanos por anti-bot y delegación DNS
- Solución/decisión:
  - se adoptó estrategia `Cloudflare Free + Cloudflare Tunnel`
  - se separó claramente entre edge local estable y edge público aún incompleto
- Estado:
  - parcialmente resuelto
- Evidencia:
  - `scripts/automation/configure_cloudflare_public_edge.ps1`
  - `ops/cloudflared/`

### 2026-03-18 - Demo pública, portales y seller portal

- Prompt/objetivo:
  - crear una demo entregable y un portal de socios/revendedores
- Errores o brechas detectadas:
  - faltaba una superficie clara para partners
  - la demo requería separación de perfiles y datos dummy
- Solución/decisión:
  - se consolidaron `admin-portal`, `client-portal`, `seller-portal` y `corporate-portal`
  - se definieron credenciales demo separadas
- Estado:
  - resuelto en base funcional
- Evidencia:
  - `frontend/apps/seller-portal/`
  - `scripts/automation/seed_public_demo_data.py`

### 2026-03-18 - Reportes, arquitectura y análisis ISO

- Prompt/objetivo:
  - documentar arquitectura, diagramas, flujos y baseline ISO
- Errores o brechas detectadas:
  - documentación dispersa
  - necesidad de traducir la conversación a artefactos persistentes
- Solución/decisión:
  - se generaron documentos de arquitectura, compliance y análisis de integraciones
- Estado:
  - resuelto documentalmente
- Evidencia:
  - `docs/architecture/`
  - `docs/compliance/`
  - `.ai_context/session_logs/`

### 2026-03-19 - Servicio SMTP modular

- Prompt/objetivo:
  - agregar servicio de mensajería por email, reutilizable y listo para producción
- Errores o brechas detectadas:
  - no existía abstracción SMTP reusable
  - faltaban validación, adjuntos y pruebas
- Solución/decisión:
  - se implementó servicio SMTP desacoplado de negocio
  - configuración por entorno y script de prueba
- Estado:
  - resuelto
- Evidencia:
  - `app/services/email_service.py`
  - `tests/test_email_service.py`
  - `docs/guide/19-email-smtp-service.md`

### 2026-03-19 - API empresarial Odoo para clientes

- Prompt/objetivo:
  - permitir que clientes empresariales generen tokens API y operen facturas desde Odoo
- Errores o brechas detectadas:
  - faltaba una capa de tokens por tenant y UI de autogestión
- Solución/decisión:
  - se creó `tenant_api`, tokens aislados y sección `API Odoo` en portal cliente
- Estado:
  - resuelto
- Evidencia:
  - `app/application/tenant_api.py`
  - `frontend/apps/client-portal/src/pages/OdooIntegration.tsx`

### 2026-03-19 - Facturas recurrentes y packaging comercial

- Prompt/objetivo:
  - permitir programar facturas diarias, quincenales, mensuales o por rango personalizado
  - ubicar esa funcionalidad en el plan `Pro`, no en `Básico`
- Errores o brechas detectadas:
  - la recurrencia no existía en backend/frontend
  - faltaba decisión comercial respaldada por mercado
- Solución/decisión:
  - se creó el servicio de facturas recurrentes
  - se bloqueó por plan y se definió como feature `Pro+`
- Estado:
  - resuelto
- Evidencia:
  - `app/application/recurring_invoices.py`
  - `frontend/apps/client-portal/src/pages/RecurringInvoices.tsx`
  - `docs/guide/21-facturas-recurrentes.md`

### 2026-03-19 - Automatización DGII con Playwright

- Prompt/objetivo:
  - construir un módulo profesional y seguro para automatizar consultas en el portal DGII
- Errores o brechas detectadas:
  - no existía paquete modular
  - riesgo alto de automatizar acciones sensibles
  - necesidad de evitar uso inseguro de credenciales del chat
- Solución/decisión:
  - se creó `app/dgii_portal_automation`
  - credenciales solo por variables de entorno
  - acciones sensibles bloqueadas en `read_only` y confirmadas en `assisted`
- Estado:
  - resuelto como base técnica
- Evidencia:
  - `app/dgii_portal_automation/`
  - `tests/test_dgii_portal_automation.py`
  - `docs/guide/22-dgii-portal-automation.md`

### 2026-03-19 - Auditoría lingüística y editorial

- Prompt/objetivo:
  - revisar gramática, ortografía, claridad, consistencia terminológica y metadatos
- Errores o brechas detectadas:
  - mojibake en textos visibles
  - ausencia sistemática de tildes en varias guías
  - mezcla inconsistente de `seller`, `socios`, `partner`, `tenant`, `cliente`
  - títulos HTML incompletos o inconsistentes
- Solución/decisión:
  - se generó auditoría editorial priorizada
  - se dejó identificado que el siguiente paso es aplicar una pasada de corrección real sobre frontend, docs y metadatos
- Estado:
  - auditado, pendiente de remediación
- Evidencia:
  - conversación actual
  - `frontend/apps/*`
  - `docs/guide/*`
  - `docs/business/*`

### 2026-03-19 - Restauracion del tunel publico Cloudflare

- Prompt/objetivo:
  - revisar el error `Cloudflare Tunnel 1033`
  - dejar `admin`, `cliente`, `socios` y el borde publico nuevamente funcionales
- Errores o brechas detectadas:
  - `cloudflared` no tenia conector activo
  - la configuracion activa del tunel apuntaba `socios.getupsoft.com.do` a `127.0.0.1:18184`
  - faltaba publicar `www.getupsoft.com.do` en DNS del tunel
  - el portal de socios mostraba el selector de clientes antes de que terminara de cargar la cartera asignada
- Solucion/decision:
  - se corrigio `C:\Users\yoeli\.cloudflared\config.yml`
  - se reactivo el tunel `getupsoft-local`
  - se publico `www.getupsoft.com.do` con `cloudflared tunnel route dns`
  - se ajusto `frontend/apps/seller-portal/src/pages/EmitECF.tsx` para esperar la carga real de clientes antes de renderizar el selector
  - se recompilo el portal de socios y se repitio la suite funcional publica
- Estado:
  - resuelto para `api`, `admin`, `cliente` y `socios`
  - `www` publicado y respondiendo en Cloudflare; la propagacion/cache del resolver local puede tardar mas
- Evidencia:
  - `.ai_context/current_state/2026-03-19_public_tunnel_restored.md`
  - `.ai_context/test_evidence/2026-03-19_public_tunnel_restored_validation.md`
  - `e2e/artifacts/public_fix_retry_20260319_155543/report.html`

<!-- chat-memory:auto -->:bootstrap-memoria-conversacional-cierre-de-sesi-n-76b9f5ebd5e4:start
### 2026-03-19 - Bootstrap memoria conversacional - cierre de sesión

- Prompt útil consolidado desde sesión `bootstrap-memoria-conversacional-cierre-de-sesi-n-76b9f5ebd5e4`.
- Resumen ejecutivo:
  - Conversación: Bootstrap memoria conversacional - cierre de sesión
  - Prompts útiles detectados: 1
  - Estado agregado: informational
  - Etiquetas principales: branding, chat-memory, dgii
- Errores o brechas detectadas:
  - Ninguno.
- Soluciones o decisiones:
  - Ninguno.
- Pendientes abiertos:
  - Ninguno.
- Evidencia:
  - `.ai_context/session_logs/2026-03-19_bootstrap-memoria-conversacional-cierre-de-sesi-n_session.md`
  - `docs/prompts/2026-03-19_bootstrap-memoria-conversacional-cierre-de-sesi-n.md`
<!-- chat-memory:auto -->:bootstrap-memoria-conversacional-cierre-de-sesi-n-76b9f5ebd5e4:end

## Errores recurrentes detectados en prompts del usuario

- Pedidos de automatización de alto riesgo con credenciales o cuentas expuestas:
  - solución permanente: no reutilizar secretos del chat; exigir entorno seguro y confirmación humana
- Solicitudes de ejecutar flujos fiscales o legales en nombre del usuario:
  - solución permanente: tratar como proceso asistido, nunca automático
- Mezcla de cambios técnicos, operativos, comerciales y documentales en una misma secuencia:
  - solución permanente: consolidar memoria por dominio y dejar evidencia por hito
- Tendencia a introducir texto español sin tildes o con problemas de codificación en superficies visibles:
  - solución permanente: aplicar pasada editorial y checklist UTF-8

## Regla operativa a futuro

Desde esta fecha, cada prompt relevante debe dejar rastro persistente en:

- este archivo, si impacta memoria de largo plazo
- `.ai_context/changes_success/`, si termina en cambio concreto
- `.ai_context/current_state/`, si define estado operativo
- `.ai_context/test_evidence/`, si genera validación o prueba
