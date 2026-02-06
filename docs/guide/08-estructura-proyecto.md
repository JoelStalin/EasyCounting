# 08 — Estructura del proyecto

La siguiente tabla resume los componentes principales del repositorio getupsoft y su responsabilidad dentro de la arquitectura.

| Ruta | Descripción |
| ---- | ----------- |
| `app/` | Código fuente del backend FastAPI organizado por dominios (`auth`, `dgii`, `billing`, `sign`, `receiver`, `ri`, `shared`). Incluye modelos SQLAlchemy, esquemas Pydantic y pruebas unitarias/e2e. |
| `app/models/` | Declaraciones ORM multi-tenant, almacenes WORM y registros de auditoría con hash encadenado. |
| `deploy/` | Artefactos para ejecución local (`docker-compose`), contenedores base (`Dockerfile.api`, `Dockerfile.nginx`) y configuración de observabilidad (Prometheus/Grafana). |
| `infra/terraform/` | Módulos reutilizables (VPC, ECR, ECS, EKS, Aurora, ElastiCache, ALB, Secrets, Route53/ACM) y ambientes `staging` / `prod` con backend remoto S3+DynamoDB. |
| `infra/k8s/` | Manifests Kustomize para el despliegue en EKS (base + overlays `staging`/`prod`) con Ingress TLS 1.3, HPA, PodMonitor y External Secrets. |
| `frontend/` | Monorepo pnpm con los portales Admin y Client (React+Vite+Tailwind+shadcn/ui), así como paquetes compartidos `@getupsoft/ui` y `@getupsoft/api-client`. |
| `scripts/` | Utilidades operativas (`setup_env.py`, `encrypt_env.py`, `sample_curl.sh`). |
| `docs/guide/` | Documentación técnica, flujos DGII, cumplimiento y checklists de certificación. |
| `.github/workflows/` | Pipeline CI/CD segmentado (`backend-ci`, `frontend-ci`, `dast-zap`) con pruebas, SAST, build de imágenes y escaneo OWASP ZAP. |

> **Tip:** El backend detecta automáticamente el uso de SQLite en pruebas y crea el esquema en memoria. Para entornos reales se ejecutan las migraciones Alembic definidas en `alembic/`.
