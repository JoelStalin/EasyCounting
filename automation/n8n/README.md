# n8n DGII Autoasistido

## Levantar n8n OSS

```bash
docker compose -f automation/n8n/docker-compose.n8n.yml up -d
```

## Importar workflow base

1. Abrir `http://localhost:5678`.
2. Importar `automation/n8n/workflows/dgii_postulacion_autoasistida_v1.json`.
3. Configurar `apiBase` e `internalSecret` en el payload de entrada.

## Payload sugerido para webhook start

```json
{
  "apiBase": "http://127.0.0.1:8000",
  "internalSecret": "dev-hmac",
  "intakePayload": {
    "rnc": "131234567",
    "razon_social": "Empresa Demo SRL",
    "tipo_contribuyente": "juridica",
    "delegado_nombre": "Juan Perez",
    "delegado_identificacion": "00112345678",
    "delegado_correo": "juan@empresa.com",
    "delegado_telefono": "8095551234",
    "delegado_cargo": "Gerente",
    "psc_preferida": "AVANSI",
    "usa_facturador_gratuito": false,
    "ofv_habilitada": true,
    "alta_ncf_habilitada": true,
    "responsable_ti": "ti@empresa.com",
    "responsable_fiscal": "fiscal@empresa.com",
    "ambiente_objetivo": "test"
  }
}
```

## Estados recomendados

`INTAKE_RECEIVED -> PRECHECK_OK -> EXPEDIENTE_LISTO -> PORTAL_LOGIN -> FORM_COMPLETADO -> ADJUNTOS_CARGADOS -> HUMAN_APPROVAL_PENDING -> SUBMIT_DONE -> TRACKID_CAPTURED -> POLLING_STATUS -> DONE/FAILED`
