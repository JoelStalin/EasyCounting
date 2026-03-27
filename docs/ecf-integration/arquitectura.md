# Arquitectura DGII e-CF (Plan Milimetrico)

## Resumen
La integracion DGII se consolida sobre `app/dgii/client.py`, `app/security/xml_dsig.py` y `app/application/ecf_submission.py`.

## Diagrama textual
1. InvoiceDomainService -> XmlBuilderService
2. XmlBuilderService -> XsdValidatorService
3. XsdValidatorService -> CertificateProvider
4. CertificateProvider -> XmlSignatureService
5. XmlSignatureService -> XmlSignatureVerificationService
6. XmlSignatureVerificationService -> DgiiAuthenticationService
7. DgiiAuthenticationService -> DgiiRecepcionService
8. DgiiRecepcionService -> DgiiSubmissionRepository
9. DgiiSubmissionRepository -> DgiiConsultaService
10. DgiiConsultaService -> PollTrackIdUseCase
11. PollTrackIdUseCase -> SecurityCodeService / QrPayloadService
12. Todo el flujo -> FiscalOperation / DGIIAttempt / EvidenceArtifact

## Gate por fase
- F0: diagnostico + diff conceptual + riesgos
- F1: contratos IO por servicio
- F2: fail-fast de secretos
- F3: XSD previo a firma
- F4: firma valida + anti-mutacion
- F5: token cache + refresh
- F6: TrackId persistido + polling
- F7: codigo seguridad + QR
- F8: logging con correlacion
- F9: matriz funcional completa + evidencias
