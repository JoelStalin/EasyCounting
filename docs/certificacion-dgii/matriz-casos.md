# Matriz de Casos Funcionales DGII

| ID | Nombre | Objetivo | Precondiciones | Datos | Pasos | Resultado esperado | Logs esperados | Persistencia esperada | Criterio de aceptacion |
|---|---|---|---|---|---|---|---|---|---|
| F001 | XML sin firmar a firmado | Validar firmado exitoso | Certificado valido | XML valido | Construir, validar, firmar | Firma creada | evento SIGNING | fingerprint + xml firmado | validacion local ok |
| F002 | Verificacion local positiva | Verificar XML firmado | XML firmado | XML firmado | Verificar firma | valido | evento VERIFY_OK | estado tecnico OK | valid=true |
| F003 | Mutacion de 1 caracter | Detectar alteracion | XML firmado | XML alterado | Verificar firma | invalido | evento VERIFY_FAIL | error almacenado | valid=false |
| F004 | Whitespace alterado | Documentar comportamiento | XML firmado | XML con whitespace alterado | Verificar | resultado documentado | warning detalle canonicalizacion | evidencia test | resultado consistente |
| F005 | Certificado valido | Permitir firmado | Certificado vigente | P12 correcto | Firmar | firmado permitido | cert metadata | metadata cert | paso permitido |
| F006 | Certificado expirado | Bloquear firmado | Cert expirado | P12 expirado | Firmar | bloqueado | error cert_expired | error persistido | bloqueo confirmado |
| F007 | Password incorrecta | Error controlado | P12 existe | Password mala | Cargar cert | error | cert_password_error | error persistido | error tipado |
| F008 | XML fuera XSD | Bloqueo antes de firma | XSD disponible | XML invalido | Validar XSD | falla | xsd_validation_failed | no firma | bloqueo previo |
| F009 | Semilla DGII | Firma semilla exitosa | Auth endpoint | semilla xml | Obtener y firmar | token workflow continuo | auth_seed_ok | evidencia auth | flujo auth sigue |
| F010 | Token obtenido | Habilitar envio | Credenciales correctas | semilla firmada | Solicitar token | token valido | auth_token_ok | cache token | envio permitido |
| F011 | Envio exitoso | Persistir TrackId | XML firmado + token | payload valido | Enviar DGII | trackId recibido | submit_success | DGIIAttempt + trackId | trackId no nulo |
| F012 | Consulta Aceptado | Actualizar estado | TrackId existente | estado aceptado | Consultar | estado aceptado | status_update | Invoice/FiscalOperation | estado final correcto |
| F013 | Consulta Rechazado | Persistir motivo | TrackId existente | estado rechazado | Consultar | estado rechazado | status_rejected | motivo rechazo | trazabilidad completa |
| F014 | Consulta Aceptado Condicional | Persistir condicion | TrackId existente | estado condicional | Consultar | condicional | status_conditional | estado condicional | mapeo correcto |
| F015 | En Proceso y reconsulta | Polling seguro | TrackId existente | estado en proceso | Polling | reconsulta | polling_iteration | historial eventos | no perdida de estado |
| F016 | Timeout recepcion | Reintento seguro | Endpoint lento | timeout | Enviar con retry | eventual exito o error tipado | retry_timeout | intentos | sin duplicidad |
| F017 | Error 500 DGII | Backoff + retry | endpoint 500 | error servidor | Enviar | retry aplicado | retry_http_5xx | intentos persistidos | politica de retry |
| F018 | Reintento sin duplicar | Garantizar idempotencia | llave idempotencia | mismo payload | reenviar | respuesta cache/reuso | idempotency_hit | sin nuevos docs | no duplicado |
| F019 | No refirma XML ya firmado | Evitar doble firma | XML ya firmado | xml firmado | pasar por servicio | bloqueo o no-op | already_signed | no mutacion | control activo |
| F020 | Codigo seguridad correcto | Derivacion reproducible | datos persistidos | invoice + fingerprint | derivar codigo | codigo estable | security_code_generated | codigo en invoice | reproducible |
| F021 | QR correcto | Payload consistente | datos persistidos | invoice + estado | generar QR payload | payload correcto | qr_payload_generated | valor persistido | coincide con datos |
| F022 | Rotacion certificado | Flujo con nuevo cert | nuevo cert vigente | cert rotado | firmar y enviar | exito | cert_rotation_ok | metadata nueva | sin downtime funcional |
| F023 | Cert ambiente incorrecto | Bloqueo por ambiente | env cert/prod | cert mismatch | validar cert | bloqueado | cert_env_mismatch | error persistido | bloqueo confirmado |
| F024 | Logs redactados | Evitar fuga secretos | logging activo | token/password | emitir logs | secretos ocultos | redaction_applied | evidencia test | sin secretos visibles |
| F025 | Persistencia completa | Guardar request/response/TrackId | envio exitoso | payload/resp | persistir | registro completo | persist_submission | DGIIAttempt completo | campos completos |
| F026 | RI correcta | Trazabilidad impresa | invoice aceptada | data fiscal | generar RI | RI consistente | ri_rendered | ruta RI | trazable |
| F027 | Separacion ambientes | Evitar cruces | config por ambiente | env test/cert/prod | validar settings | correcto | env_validation_ok | config validada | sin endpoint cruzado |
| F028 | Polling sin carreras | Evitar duplicados polling | multiples workers | mismo TrackId | ejecutar polling | sin carreras | polling_lock | un estado final | idempotente |
| F029 | Recuperacion pendientes | Reanudar tras reinicio | pendientes en DB | operaciones en proceso | iniciar jobs | recupera pendientes | recovery_started | continuidad estados | no perdida |
| F030 | Regresion completa | Proteger flujo global | suite completa | casos DGII | ejecutar suite | todo estable | regression_passed | evidencias | release gate aprobado |
