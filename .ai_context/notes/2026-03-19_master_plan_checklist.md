# Checklist residual actualizado

Fecha de corte: 2026-03-19

## P0 cerrados

- [x] Social auth implementado para Google, Facebook y Apple.
- [x] MFA basado en `challengeId`.
- [x] Tenant preliminar para auto-registro social del portal cliente.
- [x] Tours autoguiados por primera vista con persistencia backend.
- [x] Relanzamiento manual del tour desde cada portal.
- [x] Servicio SMTP modular y reusable.
- [x] Ruta publica de `RI` enlazada al renderer real.
- [x] Corporate portal implementado con producto `Accounting Management`.
- [x] Edge local ampliado para admin, client, seller, corporate y api.
- [x] Validacion Selenium en Chrome.
- [x] Validacion Selenium en Edge.

## P1 abiertos

- [ ] Persistir `cloudflared` como servicio del sistema o reemplazo equivalente.
- [ ] Publicar `www.getupsoft.com.do` de forma estable en el edge publico real con callback OAuth verificado extremo a extremo.
- [ ] Bridge runtime vivo con Odoo para sincronizacion operativa bidireccional.
- [ ] Endurecer el entorno demo con politica completa de `demo / debug local / preview privada`.

## P2 abiertos

- [ ] Rebrand completo cuando se cierre el nombre comercial del producto.
- [ ] Reescritura `getupsoft_l10n_do_pos` a Odoo 19/OWL.
- [ ] Limpieza estructural de duplicados `src/*.ts(x)` y `src/*.js` en los frontends.
- [ ] Endurecimiento adicional de CI/CD y retiro de ruido externo heredado del host.

## Bloqueos externos

- [ ] Certificacion DGII real `PRECERT/CERT/PROD`.
  - Requiere certificado `.p12`, credenciales vigentes y ejecucion asistida ante DGII.
- [ ] Publicacion real de reportes DGII desde Odoo hacia DGII.
  - Requiere definir si sera flujo guiado OFV o integracion formal soportada por el cliente.

## Credenciales demo vigentes

- `admin@getupsoft.com.do / ChangeMe123!`
- `cliente@getupsoft.com.do / Tenant123!`
- `seller@getupsoft.com.do / Seller123!`
- `seller.auditor@getupsoft.com.do / SellerAudit123!`
