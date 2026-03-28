# 08 - Timeline Real Viafirma para Obtencion de `.p12` (2026-03-27)

Fuente: evidencia visual del operador en portal Viafirma RA.

## Secuencia registrada
1. `2026-03-27 13:39` - `Solicitud recibida`
2. `2026-03-27 13:58` - `Pago completado`
3. `2026-03-27 14:01` - `Acreditacion finalizada`
4. `2026-03-27 14:05` - `La identificacion no coincide`
5. `2026-03-27 14:05` - `El tipo de documento no coincide`
6. `2026-03-27 14:10` - `Los datos de su solicitud coinciden con los de su ...`
7. `2026-03-27 14:14` - `Firma completada`
8. `2026-03-27 14:54` - `Solicitud enviada para la obtencion del certificado...`

## Estado funcional derivado
- El portal muestra bloque `Download certificate` con mensaje:
  - `Your certificate has been generated correctly. You can download it from here.`
- Conclusión operativa:
  - etapa legal/humana cerrada;
  - certificado generado por PSC;
  - siguiente etapa automatizable: descarga/ingesta segura y validacion tecnica del `.p12`.

## Checkpoint para continuidad
- Mantener estado de caso en `PSC_APPROVED` -> `CERTIFICATE_RECEIVED` al registrar ingreso del archivo.
- Si la descarga la hace operador:
  - registrar hash SHA-256 y metadatos;
  - ejecutar `validate-certificate`;
  - almacenar secreto;
  - continuar con `smoke-sign` y postulacion real DGII.
