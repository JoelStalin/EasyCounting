# 15 — Guía paso a paso de implementación en AWS

Esta guía describe un recorrido detallado para desplegar la plataforma getupsoft en AWS cumpliendo los requisitos de seguridad, disponibilidad y cumplimiento (ISO/IEC 25010, PCI DSS 4.0, OWASP 2025). Cada sección presenta los pasos recomendados, herramientas y puntos de control antes de avanzar al siguiente hito.

## 1. Preparación de la cuenta y gobierno
1. **Crear la organización y cuentas dedicadas**: utilice AWS Organizations con al menos tres cuentas (producción, staging, herramientas). Aplique Service Control Policies (SCP) para restringir servicios no requeridos.
2. **Configurar usuarios federados**: habilite AWS IAM Identity Center (ex AWS SSO) con integración de su directorio corporativo. Cree grupos `PlatformAdmins`, `SecOps`, `DevOps` y asigne permisos mínimos necesarios.
3. **Protección del root account**: MFA obligatorio, acceso solo para tareas de facturación o soporte.
4. **Configurar CloudTrail y GuardDuty**: habilítelos a nivel organización, enviando logs a una cuenta central de seguridad.

## 2. Diseño de red (VPC)
1. **Crear VPC multi-AZ**: subredes públicas (ALB/ELB) y privadas (ECS/EKS, RDS, Redis) en al menos tres zonas de disponibilidad.
2. **Configurar rutas y NAT**: subredes privadas acceden a internet mediante NAT Gateway redundante; restringir rutas a servicios necesarios.
3. **Security Groups**:
   - ALB: permitir `443` desde internet con AWS WAF.
   - Servicios internos: permitir tráfico solo desde SG de origen (por ejemplo, ECS → RDS 5432, ECS → Redis 6379).
4. **Network ACLs**: reglas restrictivas para subredes públicas y privadas.

## 3. Gestión de secretos y llaves
1. **AWS Secrets Manager**: almacenar credenciales de DB, JWT, HMAC, contraseñas de `.p12`. Utilizar rotación automática con Lambda cuando aplique.
2. **AWS KMS**: crear llaves administradas para cifrar Secrets Manager, EBS, S3 y generar `p12_kms_key` para cada tenant.
3. **Parameter Store (SecureString)**: almacenar configuraciones no sensibles (`DGII_ENV`, URLs frontales).

## 4. Almacenamiento de archivos y WORM
1. **S3 buckets**:
   - `getupsoft-ri` (RI PDF) y `getupsoft-xml` (XML e-CF/RFCE/ANECF) con cifrado SSE-KMS.
   - Habilitar Versioning + Object Lock (modo compliance) para cumplimiento WORM.
2. **Políticas IAM**: permitir acceso únicamente a roles del backend mediante `aws:PrincipalTag=tenant_id` para aislar tenants si se usa separación lógica.
3. **Lifecycle policies**: mover objetos a Glacier Deep Archive según retención legal.

## 5. Base de datos y cache
1. **RDS for PostgreSQL 14**: despliegue Multi-AZ, Storage autoscaling, Performance Insights. Configure parámetros `rds.force_ssl=1` y acceso restringido por SG.
2. **Redis (Amazon ElastiCache)**: modo cluster, subredes privadas, cifrado en tránsito y en reposo habilitado.
3. **Backups**: políticas automáticas diarias con retención ≥ 30 días y snapshots manuales previos a releases.

## 6. Contenedores y registros
1. **Amazon ECR**: crear repositorios `getupsoft/api`, `getupsoft/nginx`, `getupsoft/admin-portal`, `getupsoft/client-portal`.
2. **Políticas de escaneo**: activar escaneo con Amazon Inspector y rechazar despliegues con vulnerabilidades críticas.
3. **Pipeline de imagen**: GitHub Actions publica imágenes con tags `main-{sha}`, `release-{semver}` y configura expiración de imágenes obsoletas.

## 7. Plataforma de ejecución
Seleccione la opción acorde a la madurez del equipo:

### Opción A — Amazon ECS Fargate
1. Crear `Cluster` ECS con capacity providers Fargate/Fargate Spot.
2. Definir `Task Definitions` para `api` y `worker` con sidecar `aws-otel-collector` para métricas/logs.
3. Configurar `Service` detrás de un Application Load Balancer (ALB) con listeners 443 y certificados de ACM.
4. Habilitar auto scaling basado en CPU (60%) y latencia (ALB target response time).

### Opción B — Amazon EKS
1. Aprovisionar clúster con eksctl o Terraform, habilitando IRSA.
2. Instalar add-ons: AWS Load Balancer Controller, Cluster Autoscaler, Prometheus Operator, Fluent Bit.
3. Definir `Namespace` `getupsoft`, despliegues `api`, `worker`, `receiver`, `odoo-integration`.
4. Configurar ingress con ALB + ACM y políticas de red con Calico/OPA Gatekeeper.

## 8. Despliegue de backend
1. **Variables de entorno**: mapear Secrets Manager → ECS/EKS Task env. Incluir `LOG_LEVEL`, URLs DGII, credenciales DB.
2. **Migraciones**: ejecutar `alembic upgrade head` mediante `Job` (EKS) o `one-off task` (ECS) antes de actualizar servicios.
3. **Escalabilidad horizontal**: mínimo 2 réplicas por servicio en producción; habilitar circuit breakers y timeouts en configuraciones de FastAPI/Uvicorn.
4. **TLS interno**: usar ACM Private CA para emitir certificados internos si se requieren mTLS entre servicios.

## 9. Frontend (React Portals)
1. **Build**: ejecutar `pnpm build` para cada portal; publicar artefactos en S3 (`admin-portal`, `client-portal`).
2. **CloudFront**: distribuir cada portal con certificados ACM y `origin access control` (OAC) al bucket S3.
3. **WAF**: agregar reglas OWASP Top 10 y protección de bots.
4. **Autenticación**: configurar dominio personalizado (Route 53) con registros `admin.example.com`, `app.example.com` apuntando al CloudFront correspondiente.

## 10. Observabilidad y auditoría
1. **Logs**: enviar stdout/stderr de contenedores a CloudWatch Logs y replicar a Amazon OpenSearch o Loki (via Prometheus stack) según preferencia.
2. **Métricas**: desplegar Prometheus + Grafana administrados (Amazon Managed Grafana/Prometheus) o autogestionados; configurar dashboards para latencia API, colas, RDS, costos.
3. **Alertas**: integrar CloudWatch Alarms con SNS/Slack para errores 5xx, latencia, fallos de jobs, storage S3 cercano al límite.
4. **Auditoría**: habilitar AWS Config, CloudTrail Lake y almacenar `audit_logs` de la app en S3 con Object Lock.

## 11. Seguridad avanzada y cumplimiento
1. **WAF + Shield Advanced** para proteger ALB y CloudFront.
2. **Inspector** para escanear instancias, contenedores y Lambda.
3. **Security Hub**: activar controles PCI DSS 4.0 y resolver hallazgos críticos.
4. **Backups cifrados**: verificar KMS y políticas de separación de llaves (producción vs. staging).
5. **Revisiones periódicas**: realizar tabletop exercises y pruebas de recuperación de desastres cada trimestre.

## 12. CI/CD
1. Configurar GitHub Actions con OpenID Connect (OIDC) para asumir roles en AWS sin claves de acceso.
2. Pipeline propuesto:
   - **Build & Test**: ejecutar linters, pytest, Cypress (modo headless) con mocks.
   - **Security**: OWASP Dependency-Check, SAST (bandit), DAST (ZAP baseline), escaneo de contenedores.
   - **Deploy**: publicar imágenes en ECR, aplicar Terraform/CloudFormation, invalidar CloudFront.
3. Implementar revisiones manuales (manual approval) para producción y firmar artefactos (cosign/slsa).

## 13. Checklist previo a go-live
- ✅ DRP documentado y probado.
- ✅ Monitoreo en tiempo real (CloudWatch dashboards + Grafana).
- ✅ Alertas y runbooks vinculados a incident response.
- ✅ Revisiones de cumplimiento (PCI DSS scope, protección de datos).
- ✅ Pen-test o revisión interna de seguridad completada.

## 14. Mantenimiento continuo
1. Programar parches mensuales de dependencias y AMIs base.
2. Revisar costos con AWS Cost Explorer y activar budgets con alertas.
3. Auditar accesos IAM trimestralmente.
4. Actualizar documentación (docs/guide) con cambios de arquitectura o nuevos servicios.

> **Resultado esperado**: una plataforma getupsoft desplegada en AWS con infraestructura reproducible, observabilidad completa y controles de seguridad alineados a las normas exigidas.
