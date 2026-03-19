# Reglas Lingüísticas y Metadatos (Auditoría Permanente)

## 1. Prompts Almacenados
* **Prompt de Tutor Interactivo:** "Crear un sistema de ayuda guiada dentro del portal demo... Tutor contextual por campo, modo tutorial automático, asistencia inteligente..."
* **Prompt de Auditoría Lingüística:** "Auditoría completa del idioma (Gramática, Ortografía, Estilo, Consistencia, Metadatos)... Mantener el español natural, correcto y profesional..."

## 2. Reglas Globales de Redacción a Futuro
Al escribir copies para UI, crear nuevas páginas, o generar metadatos, los próximos agentes deben aplicar EXCEPCIÓN CERO a estas reglas:
- **Acentuación Estricta:** Reemplazar de inmediato cualquier falta de tildes dejadas por desarrolladores en el código fuente (ej. *menu -> menú*, *aqui -> aquí*, *emision -> emisión*, *informacion -> información*). La excusa de "es un string en código" es inválida.
- **Formato de Siglas:** Se usará estrictamente `e-CF`, `DGII`, `RNC`, y `ITBIS` siempre en mayúsculas sostenidas, excepto el sufijo 'e-' de electrónico.
- **Estilo:** Directo, asertivo, sin redundancias. En interfaces de validación como la de Comprobantes Fiscales se debe hablar de "Obligatorio" u "Opcional" explícitamente y nunca usar verbos dubitativos.
- **Tono Premium:** El tono es de una plataforma corporativa sólida y transparente, la redacción no puede ser excesivamente coloquial ("hola amiguito") ni muy opaca gubernamental ("de acuerdo a la norma general número x, el contribuyente pre-inscripto..."). Equilibrio B2B.

## 3. Metadatos
Se deben generar y optimizar siempre las etiquetas SEO (`<title>`, `<meta name="description">`) cuidando que el tamaño no supere los límites para SERP y evite la canibalización de keywords transaccionales (`Facturación e-CF`, `Emisor Electrónico`).
