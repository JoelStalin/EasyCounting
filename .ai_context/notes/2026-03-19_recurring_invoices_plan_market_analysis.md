# Analisis de mercado: facturas recurrentes desde Pro

Fecha de corte: 2026-03-19.

## Hallazgos

- La DGII mantiene `Facturador Gratuito`, pero su propia FAQ indica limitaciones claras para automatizacion empresarial: no se interconecta con sistemas internos y los datos del comprador deben capturarse al momento de emitir. Fuente:
  - https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Preguntas%20frecuentes/Generales/Preguntas-Frecuentes-Facturador-Gratuito.pdf
- En el mercado local, los proveedores comerciales separan la capa base de emision de las capacidades operativas avanzadas:
  - `DigitalHorizon` publica escalera desde `RD$990/mes` hasta `RD$19,900/mes`, con addons ERP y modulos por separado, lo que confirma que automatizacion y operacion ampliada se monetizan por encima del plan de entrada.
    - https://digitalhorizonrd.com/
  - `Factoa` publica planes mensuales `Avanzados` y `Plus`, donde los modulos superiores concentran funciones operativas adicionales como reportes, cuentas por cobrar/pagar, POS y configuraciones ampliadas.
    - https://factoa.net/home-rd
  - `Alegra RD` publica escalera `Emprendedor`, `PyME`, `PRO` y `PLUS`, con el salto de `PRO` y superiores como referencia de capacidades ampliadas para negocios en crecimiento.
    - https://www.alegra.com/rdominicana/contabilidad/precios/

## Decision aplicada al producto

- `Basico / Emprendedor`: sin facturas recurrentes.
- `Pro / Profesional`: con facturas recurrentes.
- `Enterprise`: con facturas recurrentes.

## Razon

Las facturas recurrentes son una automatizacion operativa que reduce trabajo manual, habilita ciclos de cobro y agrega valor recurrente al cliente empresarial. Eso las ubica mejor en `Pro` que en el plan basico de emision.
