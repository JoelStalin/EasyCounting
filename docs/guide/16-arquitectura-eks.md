# 16 — Arquitectura de Microservicios y Plan de Despliegue en AWS EKS

Este documento describe en detalle la arquitectura de referencia de getupsoft y el plan de despliegue sobre Amazon Elastic Kubernetes Service (EKS). El objetivo es proveer una guía accionable que cumpla con los requisitos de multi-tenancy, seguridad (ISO/IEC 25010, PCI DSS 4.0, OWASP Top 10 2025) y las exigencias normativas de la DGII para el manejo de Comprobantes Fiscales Electrónicos (e-CF).

---

## 1. Visión general

getupsoft se compone de microservicios Python/FastAPI y procesos asíncronos que corren en contenedores. Cada servicio expone API REST protegidas con JWT, MFA TOTP y RBAC multi-tenant. Los artefactos se empaquetan como imágenes OCI y se orquestan en Kubernetes. Los portales web (Admin y Client) se entregan como aplicaciones SPA servidas desde S3/CloudFront y consumen la API vía un Ingress TLS 1.3.

La plataforma se alinea a los principios de:

- **Separación de responsabilidades:** servicios aislados por dominio (auth, sign, billing, etc.).
- **Seguridad por diseño:** cifrado en tránsito, secreto en reposo con AES-256-GCM (config) y Argon2id para credenciales.
- **Observabilidad integrada:** métricas Prometheus, logs estructurados JSON y trazabilidad distribuida con `X-Trace-ID`.
- **Resiliencia multi-tenant:** cada solicitud se ejecuta con el `tenant_id` propagado y validado en todas las capas.

---

## 2. Catálogo de microservicios

| Servicio | Descripción | Dependencias | Endpoints destacados |
| --- | --- | --- | --- |
| **auth_service** | Gestión de identidades, MFA, sesión y RBAC. Opera sobre tablas `users`, `roles`, `permissions`. | PostgreSQL, Redis (tokens), AWS Secrets Manager (claves JWT). | `/auth/login`, `/auth/mfa/verify`, `/auth/refresh`, `/auth/rbac/roles`. |
| **sign_service** | Firma XML con XMLDSig (RSA-SHA256) ejecutando `xmlsec` y protegiendo claves P12. | Secrets Manager (certificados), AWS KMS, S3 (artefactos), Dramatiq (colas). | `/sign/xml`, `/sign/certificate/validate`. |
| **dgii_client** | Cliente resiliente DGII: obtiene semilla, firma y cachea token JWT (55 min TTL) en Redis. Control de reintentos exponenciales. | Redis, sign_service, Secrets Manager (credenciales DGII). | `/dgii/token`, `/dgii/ecf/send`, `/dgii/ecf/status`. |
| **billing_service** | Orquestador de emisión de e-CF: genera XML conforme XSD, envía a sign_service y dgii_client, persiste resultados y programa RI en PDF. | PostgreSQL, S3 (XML/RI), Dramatiq, sign_service, dgii_client. | `/tenant/emit/ecf`, `/tenant/invoices`, `/tenant/ri/{id}`. |
| **approval_flow** | Controla ARECF/ACECF, notificaciones y estados. | PostgreSQL, Redis (colas), Email/SMS providers. | `/tenant/approvals`, `/tenant/approvals/{id}/send`. |
| **plans_service** | Gestión de planes tarifarios y cálculo de comisiones (FIJO, PORCENTAJE, MIXTO, ESCALONADO + overrides). | PostgreSQL. | `/admin/plans`, `/tenant/plans/current`, `/tenant/plans/preview`. |
| **admin_service** | Administra tenants, auditoría, métricas plataforma. Scope de roles `PLATFORM`. | PostgreSQL, audit logs API. | `/admin/companies`, `/admin/metrics`. |
| **client_service** | Backend Portal Cliente con endpoints multi-tenant y reportes. | PostgreSQL, S3 (descargas). | `/tenant/dashboard`, `/tenant/certificates`. |
| **logger_service/compliance** | Recibe logs de auditoría inmutables, encadena hashes SHA-512 y almacena en S3 Object Lock. | PostgreSQL (índices), S3 WORM, KMS. | `/audit/logs`, `/audit/verify`. |
| **odoo_integration** (opcional) | Microservicio desacoplado JSON-RPC → Odoo 18 con colas idempotentes. | PostgreSQL, Dramatiq, HMAC inter-servicio. | `/odoo/sync/invoice`, `/odoo/webhook`. |

Cada servicio expone `/healthz`, `/readyz` y `/metrics`. Los contenedores usan `gcr.io/distroless/python3` hardened con user no-root (`uid 10001`).

---

## 3. Integración y flujo de datos

1. **Autenticación**: usuario → auth_service → JWT (15 min) + Refresh (8 h). MFA TOTP validado contra Redis (ventana temporal configurable).
2. **Emisión e-CF**:
   1. billing_service valida payload según `schemas/` (XSD DGII).
   2. Sign_service firma XML con certificado del tenant (descargado de Secrets Manager y cacheado en tmpfs en memoria, nunca disco persistente).
   3. dgii_client obtiene token (cache Redis) y ejecuta `POST /Recepcion/e-CF`.
   4. Respuesta se persiste en `invoices`, se calcula tarifa (`plans_service.calculate_fee`) y se genera tarea Dramatiq para RI.
3. **Auditoría**: cada acción relevante envía evento a logger_service con `hash_prev`, `hash_curr` y `tenant_id`.
4. **Frontends**: React apps autenticadas mediante `Authorization: Bearer` (Access Token). Los permisos se cargan en `useAuth()` y protegen rutas.

---

## 4. Seguridad y cumplimiento

- **Cifrado**: TLS 1.3 (ACM certificados), Secrets cifrados con AES-256-GCM bajo KMS, archivos firmados con XMLDSig RSA-SHA256.
- **Identidades**: Argon2id con parámetros `time_cost=4`, `memory_cost=64MB`, `parallelism=2`. Refresh tokens rotados y revocados en Redis.
- **RBAC**: permisos codificados en tablas `role_permissions`. Multi-tenant enrutado a través de `X-Tenant-ID` + JWT `tenant_id`. Validación cruzada en middleware.
- **PCI DSS**: segmentación de red, logging inmutable, monitoreo continuo, escaneo vulnerabilidades (GitHub Actions + AWS Inspector).
- **OWASP Top 10**: validación estricta de inputs (Pydantic), rate limiting por tenant (nginx-ingress + Redis), protección CSRF (cookies `SameSite=strict`).

---

## 5. Observabilidad

- **Logs**: JSON con claves `timestamp`, `level`, `service`, `trace_id`, `tenant_id`. Enviados a Fluent Bit → Loki y replicados a CloudWatch.
- **Métricas**: `/metrics` expone latencias, contadores DGII, tiempos de firma. Prometheus scrapea via `ServiceMonitor`. Alertmanager notifica a Slack/SNS.
- **Trazas**: OpenTelemetry SDK exporta a OTLP collector → Tempo/X-Ray.

---

## 6. Topología EKS

1. **Cluster**: `eksctl`/Terraform crea clúster con versión >=1.29, dos node groups (general purpose y compute intensivo para sign_service). Nodes con Bottlerocket OS.
2. **Namespaces**:
   - `getupsoft-system`: controladores (ingress, cert-manager, external-secrets).
   - `getupsoft-app`: microservicios productivos.
   - `getupsoft-observability`: Prometheus, Grafana, Loki, Tempo.
3. **Networking**: CNI Calico con políticas de red `deny-all` y reglas específicas por servicio. Service Mesh opcional (AWS App Mesh o Istio) para mTLS interno.
4. **IRSA**: cada Deployment cuenta con ServiceAccount asociado a un rol IAM mínimo (por ejemplo `getupsoft-sign-secrets` con permiso `secretsmanager:GetSecretValue`).
5. **Storage**: EFS CSI para compartir plantillas RI, EBS para bases de datos estadoful (si aplica). Preferible RDS/Aurora externo.
6. **Escalado**: HPA configurado por CPU (60%), latencia (Prometheus Adapter) y `QueueDepth` (Dramatiq). Cluster Autoscaler habilitado.

---

## 7. Proceso de aprovisionamiento (Terraform)

1. **Estado remoto**: bucket S3 `getupsoft-terraform-state` cifrado + DynamoDB `terraform-lock`.
2. **Módulos**:
   - `network`: VPC / subredes / NAT / route tables.
   - `eks`: cluster, node groups, addons.
   - `rds`: Aurora PostgreSQL Multi-AZ.
   - `redis`: Elasticache cluster.
   - `security`: Secrets Manager, KMS keys, IAM roles (IRSA).
   - `observability`: Managed Prometheus/Grafana (opcional) y buckets S3 (RI, XML, logs auditoría).
3. **Outputs**: `kubeconfig`, ARNs de roles, endpoints DB/Redis, nombres buckets.
4. **Validaciones**: Terraform `validate`, `plan`, `apply` en pipeline GitHub Actions usando OpenID Connect (sin llaves largas).

---

## 8. Manifiestos Kubernetes (Kustomize)

La estructura recomendada se incluye en `deploy/k8s/`:

```
deploy/k8s/
├── base
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── rbac
│   │   └── tenants-network-policy.yaml
│   ├── config
│   │   ├── configmap-common.yaml
│   │   └── secret-generic.yaml        # plantilla para ExternalSecrets
│   └── services
│       ├── auth
│       │   ├── deployment.yaml
│       │   └── service.yaml
│       └── ...
├── overlays
│   ├── staging
│   │   ├── kustomization.yaml
│   │   └── patch-hpa.yaml
│   └── production
│       ├── kustomization.yaml
│       ├── patch-hpa.yaml
│       └── patch-pdb.yaml
└── README.md
```

- **External Secrets Operator** sincroniza secretos desde Secrets Manager mediante `ClusterSecretStore`.
- **Parches**: overlays ajustan réplicas, recursos, dominios, rutas de Ingress y configuraciones de observabilidad.
- **Jobs**: `alembic-migrate.yaml` se ejecuta como `Job` antes de cada despliegue (trigger manual o Argo Rollouts hook).

---

## 9. Pipeline CI/CD

1. **Build**: GitHub Actions ejecuta `poetry check`, `pytest --cov`, `npm test`, `cypress run`, `bandit`, `semgrep`, `dependency-check`.
2. **Imagen**: `docker buildx build` con etiquetas `main-{sha}` y `release-{semver}` firmadas con cosign. Push a Amazon ECR.
3. **Infra**: workflow aplica Terraform (staging → producción con aprobación manual).
4. **Deploy**: `kubectl apply -k deploy/k8s/overlays/{env}` usando `aws eks update-kubeconfig`. Rollback con `kubectl rollout undo` o versión anterior de imagen.
5. **Post-deploy**: smoke tests (locust/ginkgo) y validación DGII sandbox mediante scripts en `scripts/dgii_check.py` (mocked en staging).

---

## 10. Operación continua

- **Runbooks**: ver `docs/guide/12-scripts-operativos.md` para troubleshooting DGII, rotación certificados, reseteo colas.
- **Mantenimiento**: parches mensuales, revisión costos, pruebas DRP semestrales, rotación llaves KMS anual.
- **Alertas clave**: fallos en firma XML, caducidad certificados (<30 días), backlog Dramatiq > 200 mensajes, errores DGII consecutivos > 5.

---

## 11. Checklist previo al despliegue EKS

1. Terraform plan sin cambios pendientes.
2. Certificados TLS (ACM) cargados y validados.
3. Secrets Manager poblado (`/getupsoft/{env}/database`, `/getupsoft/{env}/redis`, `/getupsoft/{tenant}/p12`).
4. Reglas de Firewall/NetworkPolicy verificadas (pods solo comunican lo necesario).
5. Dashboards Grafana publicados y alertas en SNS/Slack activas.
6. Plan de rollback documentado (imágenes previas + snapshot DB/Redis + backups S3).

---

## 12. Referencias

- [DGII — Especificaciones Técnicas e-CF](https://dgii.gov.do/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [OWASP SAMM 2.0](https://owaspsamm.org/)
- [NIST SP 800-63B — Digital Identity Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)

Este documento debe revisarse y actualizarse en cada release mayor o cambios relevantes de infraestructura.
