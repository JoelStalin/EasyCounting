---
description: Arquitectura de Scraper OFV y Automatización de la DGII (Oficina Virtual)
---

# 🌐 Mapeo y Automatización de Oficina Virtual DGII (OFV)
Este documento funge como pilar central de diseño para la integración no-API de Certia con la DGII.

## 1. Módulos y Rutas a Automatizar (Vía Playwright/Selenium en Servidor)
Como la DGII no ofrece API Pública para declaraciones ni solicitudes, la capa `app/services/dgii_scraper` del backend asume el control:
- **Login:** `https://dgii.gov.do/ofv/login.aspx`
- **Declaraciones (Interactivas y en Cero):** Formularios ITBIS (ITI), IR-3, IR-17, etc.
- **NCF y E-CF:** Solicitudes de autorización para facturadores gratuitos y secuencias de NCF físicos.
- **Buzón:** `msgNotificaciones.aspx` para reportar notificaciones automáticamente al cliente en la plataforma Certia.

## 2. Gestión de Credenciales y MFA Token
El sistema almacenará credenciales base, pero el **Token de validación o MFA (Dispositivos de Seguridad)** será procesado de forma dinámica:
- Credencial de Ejemplo: `225007006423` / `Jm8296861202`
- **Flujo de Token Transaccional:** Si la automatización de Certia se detiene en Odoo/FastAPI debido a un reto de seguridad, el Scraper se pausará y emitirá una alerta WebSockets (Socket.io) al portal `client-portal` solicitando al usuario que ingrese el código de tarjeta de coordenadas/token digital. Una vez recibido el token, el Scraper reanuda el submit.

## 3. Modelo SaaS y Cobros
La capacidad de automatizar reportes a la DGII es un servicio *Premium/Adicional*.
- Se diseña una pantalla de roles/planes de servicios (`Persona`, `Negocios`, `Socios`, y administradores globales o `Root`).
- Las declaraciones en cero y automatizaciones de CS1 se bloquean tras un paywall (Planes de Suscripción) o RBAC dependiente del tenant.

## 4. Odoo Init Hook
La auto-configuración contable (creación de Diarios de Venta LATAM, Tipos de Documentos y Tipos de Gasto como "02" requeridos para B2B) ha sido diseñada para moverse a una función `post_init_hook` dentro del módulo `l10n_do` o la dependencia local, garantizando que el entorno no sufra `Validation Error: Fiscal invoices require partner fiscal type`. El Setup será 100% silencioso excluyendo VAT de la empresa.
