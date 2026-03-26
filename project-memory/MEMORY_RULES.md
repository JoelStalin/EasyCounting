# Memory Rules

- Cada decision relevante debe registrar fecha, fuente, impacto y archivos afectados.
- Cada corrida reproducible debe terminar en `tests/artifacts/YYYY-MM-DD_HH-mm-ss_*`.
- No se borra evidencia previa; se indexa.
- Los bloqueos externos se registran con causa exacta, no con texto ambiguo.
- La memoria distingue entre `LOCAL`, `TEST`, `CERT` y `PROD`.
- `PRECERT` queda documentado solo como alias retrocompatible de `TEST`.
- El estado del proyecto se actualiza primero en `17-change-log.md` y luego en los documentos tematicos afectados.
