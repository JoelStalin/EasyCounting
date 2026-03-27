# Checklist Operativo Paso a Paso (46 pasos)

1. Confirmar requisitos DGII del contribuyente.
2. Confirmar usuario administrador habilitado.
3. Confirmar acceso OFV y portal DGII.
4. Obtener certificado digital autorizado.
5. Validar metadata del certificado (subject/serial/vigencia).
6. Asegurar cadena de confianza del certificado.
7. Preparar secretos en gestor seguro.
8. Crear/actualizar `.env.example`.
9. Crear/actualizar schema de configuración fail-fast.
10. Detectar stack real del proyecto.
11. Ubicar módulo XML existente.
12. Ubicar módulo de facturación existente.
13. Construir XML base e-CF.
14. Validar XML contra XSD por tipo.
15. Integrar carga del certificado `.p12/.pfx`.
16. Integrar firmado XMLDSIG RSA-SHA256.
17. Integrar `KeyInfo/X509Data`.
18. Integrar verificación local de firma.
19. Integrar fingerprint anti-mutación.
20. Integrar obtención de semilla DGII.
21. Integrar firma de semilla y token.
22. Integrar cliente de recepción DGII.
23. Persistir `TrackId` y respuesta inmediata.
24. Integrar consulta por `TrackId`.
25. Integrar polling seguro de `En Proceso`.
26. Integrar manejo de estados finales e intermedios.
27. Integrar logs estructurados y masking.
28. Integrar idempotencia por llave + hash.
29. Integrar retries con backoff controlado.
30. Integrar generación de código de seguridad.
31. Integrar generación de payload QR.
32. Integrar representación impresa (si aplica).
33. Crear pruebas unitarias clave.
34. Crear pruebas de integración DGII mock.
35. Crear pruebas funcionales F001-F030.
36. Correr suite local y guardar evidencia.
37. Correr suite en CI y guardar evidencia.
38. Preparar matriz de certificación DGII.
39. Ejecutar simulación de envío/consulta.
40. Registrar evidencias (`docs/certificacion-dgii/evidencias`).
41. Corregir rechazos y errores recurrentes.
42. Congelar configuración de producción.
43. Desplegar por ambiente (TEST -> CERT -> PROD).
44. Monitorear expiración de certificado.
45. Monitorear rechazos y `En Proceso` prolongado.
46. Preparar y validar runbook de incidentes.
