# Postman Test API (DGII ENFC + Portales)

## 1) Qué incluye

- `dgii_encf_test_api.postman_collection.json`
- `local-docker.postman_environment.json`

Cubre:

- Portal Auth (`/api/v1/auth/login`, `/api/v1/me`)
- Admin API (`/api/v1/admin/...`)
- Cliente API (`/api/v1/cliente/...`)
- DGII ENFC (`/fe/...`)

## 2) Configurar el usuario admin default (bootstrap)

Por seguridad **NO** se hardcodea la clave en el repo. Configúralo en tu `.env` (local) o en variables del contenedor:

- `BOOTSTRAP_ADMIN_EMAIL=ceo@getupsoft.local`
- `BOOTSTRAP_ADMIN_PASSWORD=...`  (tu clave)
- `BOOTSTRAP_ADMIN_ROLE=platform_admin`
- `BOOTSTRAP_ADMIN_PHONE=0000000000`

### Login con `ceo`

El endpoint `/api/v1/auth/login` acepta un identificador corto: si envías `email=ceo`, el backend lo normaliza a `BOOTSTRAP_ADMIN_EMAIL`.

## 3) Importar en Postman

1. Importa la **colección**:

- `postman/test_api/dgii_encf_test_api.postman_collection.json`

2. Importa el **environment**:

- `postman/test_api/local-docker.postman_environment.json`

3. Selecciona el environment `DGII ENFC Local Docker`.

4. Ajusta variables:

- `base_url` (por defecto `http://localhost:8080`)
- `admin_email` (por defecto `ceo`)
- `admin_password`

## 4) Orden recomendado de ejecución

- `Portal Auth / Login (Admin/Cliente)`
- `Portal Auth / Me (JWT)`
- `Admin Portal API / List Tenants`
- `DGII ENFC / Semilla (GET)`

> Nota: la request `Validacion Certificado (XML firmado => token)` requiere que envíes un XML realmente firmado (SignXML). En el ambiente local puedes omitirla si no tienes el XML firmado a mano.
