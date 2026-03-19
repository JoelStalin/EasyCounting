# Real Certification Runbook

Este documento deja el flujo seguro para pruebas reales y certificacion sin usar cuentas root ni secretos expuestos en el chat.

## Guardrails

- no usar `AWS root user` para automatizacion
- no exponer `80/443` publicamente desde el equipo sin reverse proxy, TLS y allowlist
- no reutilizar credenciales DGII o AWS que ya fueron divulgadas en un chat o captura
- rotar inmediatamente cualquier secreto ya compartido

## Acciones obligatorias antes de produccion

1. Rotar la clave root de AWS y habilitar MFA.
2. Crear un usuario o rol IAM dedicado para Route53 con permisos minimos.
3. Generar `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` para ese usuario.
4. Rotar tambien la credencial DGII compartida y guardarla fuera del repo.
5. Definir el `HostedZoneId` real de `getupsoft.com`.

## IAM minimo recomendado para Route53

Permisos esperados:

- `route53:ListHostedZonesByName`
- `route53:ListResourceRecordSets`
- `route53:ChangeResourceRecordSets`
- `route53:GetChange`

Recurso:

- limitar a la hosted zone exacta de `getupsoft.com`

## Arranque seguro en WSL

Comando:

```powershell
.\scripts\automation\start_wsl_local_service.ps1
```

Puertos locales resultantes:

- `http://127.0.0.1:28080` -> Nginx local sin TLS para pruebas
- `http://127.0.0.1:18081` -> Admin SPA local
- `http://127.0.0.1:18082` -> Client SPA local
- `http://127.0.0.1:18083` -> Redirect local del apex hacia admin

Esto no publica puertos a toda la red.

## AWS CLI seguro

Configura un perfil dedicado:

```powershell
.\scripts\automation\configure_aws_route53_profile.ps1 `
  -AccessKeyId "<IAM_ACCESS_KEY_ID>" `
  -SecretAccessKey "<IAM_SECRET_ACCESS_KEY>" `
  -SessionToken "<AWS_SESSION_TOKEN_OPCIONAL>" `
  -ProfileName "getupsoft-route53"
```

## Actualizacion DNS para getupsoft.com

```powershell
.\scripts\automation\update_route53_getupsoft.ps1 `
  -HostedZoneId "<GETUPSOFT_HOSTED_ZONE_ID>" `
  -RecordNames @("getupsoft.com.","*.getupsoft.com.") `
  -ProfileName "getupsoft-route53"
```

## Flujo de certificacion DGII

1. Levantar el backend local en WSL.
2. Confirmar salud con `/health`, `/readyz` y `/api/v1/odoo/rnc/search`.
3. Configurar Odoo con `getupsoft_dgii_encf.base_url=http://host.docker.internal:8000` o la URL interna correspondiente.
4. Cargar certificados `.p12` del emisor en `secrets/`.
5. Ejecutar casos de prueba en ambiente `CERT` o `PRECERT`, no con credenciales divulgadas.
6. Conservar evidencia: XML firmado, `trackId`, respuesta DGII, consulta de estado y asiento contable.

## Lo que sigue faltando para ejecucion real completa

- confirmar la base de datos de produccion/certificacion
- definir las IPs permitidas si se desea exposicion externa controlada
- provisionar el `HostedZoneId` real de `getupsoft.com`
- entregar credenciales IAM no root, idealmente temporales con `SessionToken`
- entregar certificado `.p12` DGII rotado y su password por canal seguro
