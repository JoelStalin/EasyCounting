# Tablero KPIs y SLA

KPIs iniciales:

- `% pasos automaticos`
- `tiempo medio por paso`
- `tasa de reintentos`
- `tasa de bloqueos humanos`
- `tiempo hasta TRACKID_CAPTURED`
- `MTTR` de fallos bloqueantes

SLA sugerido:

- Reintento transitorio UI: <= 15 min
- Resolucion bloqueos humanos: <= 4 horas habiles
- Confirmacion de `TrackId`: <= 30 min desde submit
