# Matriz de Trazabilidad Prompt -> Implementacion

| Requisito | Implementacion | Test/Evidencia |
|---|---|---|
| Validar XSD antes de firmar | `app/dgii/domain/xsd_validator_service.py` | `tests/test_xsd_validation.py` |
| Firma XMLDSIG RSA-SHA256 | `app/security/xml_dsig.py`, `app/dgii/domain/xml_signature_service.py` | `tests/test_signing.py`, `tests/test_xml_dsig_service.py` |
| Verificacion local obligatoria | `app/dgii/domain/xml_signature_verification_service.py`, `app/dgii/application/sign_ecf_use_case.py` | `tests/test_signing.py` |
| Persistencia TrackId | `app/application/ecf_submission.py`, `app/models/fiscal_operation.py` | `docs/certificacion-dgii/matriz-casos.md` F011 |
| Idempotencia/retry seguro | `app/dgii/client.py` | `docs/certificacion-dgii/matriz-casos.md` F016-F018 |
| Anti-mutacion post-firma | `app/dgii/infrastructure/signed_xml_repository.py` | `docs/certificacion-dgii/matriz-casos.md` F003/F019 |
| Logs redactados | `app/core/logging.py`, `app/infra/settings.py` | `tests/test_logging_redaction.py` |
| Matriz funcional F001-F030 | `docs/certificacion-dgii/matriz-casos.md` | `tests/functional/test_dgii_f001_f030.py` |
| Contrato IA registrado | `.ai_context/notes/...`, `.ai_context/decisions/...` | revision documental |
