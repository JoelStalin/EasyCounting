---
description: Pipeline de Configuración y Pruebas Funcionales (Odoo e-CF)
---

# Prompt Principal (Fijado por el CEO)
"Investiga como parametrizar clientes proveedores el entorno contable de odoo 19 y 15, luego realiza las tareas de setting y luego enlista los casos de uso y reliza las pruebas funcionales, guarda este prompt para que siempre realices esto."

# Proceso de Inicialización y Parametrización (Odoo 15 y 19)

Según la investigación y estándares de DGII para las aplicaciones Odoo locales (Marcos, Indexa, Getupsoft):

## 0. Módulos Críticos (Pre-requisito)
El entorno **fallará silenciosamente o mostrará errores de UI** (dropdowns vacíos) si no están debidamente instalados:
- **Enterprise Modules (`account_accountant`):** Base para diarios, facturación avanzada y reportería local.
- **Localización Base (`l10n_do`, `getupsoft_l10n_do_accounting`):** Trae los catálogos XSD, tipos de NCF y posiciones fiscales.
- **Facturación Electrónica (`getupsoft_l10n_do_e_accounting`):** Orquesta el mapeo del E-CF XML y el webhook con Certia.

## 1. Compañía (Emisor)
- `country_id`: Debe ser explícitamente República Dominicana (DO).
- `vat` (RNC): Debe tener un RNC dominicano válido (9 o 11 dígitos).
- `l10n_do_ecf_issuer`: Debe estar en `True`.

## 2. Diarios Contables (Journals)
- `l10n_latam_use_documents`: Los diarios de Venta (Sales) y Compra (Purchase) deben tener activa la bandera de uso de documentos fiscales LATAM.

## 3. Contactos (Clientes y Proveedores)
- **Tipo de Identificación:** Deben tener asociado el ID del tipo de identificación (RNC o Cédula) correspondiente al esquema LATAM (`l10n_latam_identification_type_id`).
- **País:** RD.

---
# Casos de Uso a Probar Funcionalmente
Al momento de automatizar Selenium, asegúrese de ejecutar:
1.  **Factura de Crédito Fiscal (Type 31 / B2B):**
    - Requiere Cliente con RNC válido. Retorna TrackID de Certia.
2.  **Factura de Consumo (Type 32 / B2C):**
    - Cliente Consumidor Final. Comprueba envío sin RNC forzoso.
3.  **Nota de Crédito (Type 33):**
    - Modifica un Type 31 existente. Valida montos reversados hacia DGII.
