# Postman Test API (DGII ENFC + Portales)

## 1) Que incluye

- `dgii_encf_test_api.postman_collection.json`
- `local-docker.postman_environment.json`

Cubre:

- Portal Auth (`/api/v1/auth/login`, `/api/v1/me`)
- Admin API (`/api/v1/admin/...`)
- Cliente API (`/api/v1/cliente/...`)
- DGII ENFC (`/fe/...`)

## 2) Configurar el usuario admin default (bootstrap)

Por seguridad no se hardcodea la clave en el repo. Configuralo en tu `.env` local o en variables del contenedor:

- `BOOTSTRAP_ADMIN_EMAIL=admin@getupsoft.com.do`
- `BOOTSTRAP_ADMIN_PASSWORD=...`
- `BOOTSTRAP_ADMIN_ROLE=platform_admin`
- `BOOTSTRAP_ADMIN_PHONE=0000000000`

### Login con `admin`

El endpoint `/api/v1/auth/login` acepta un identificador corto: si envias `email=admin`, el backend lo normaliza a `BOOTSTRAP_ADMIN_EMAIL`.

## 3) Importar en Postman

1. Importa la coleccion:

- `postman/test_api/dgii_encf_test_api.postman_collection.json`

2. Importa el environment:

- `postman/test_api/local-docker.postman_environment.json`

3. Selecciona el environment `DGII ENFC Local Docker`.

4. Ajusta variables:

- `base_url` (por defecto `http://localhost:8080`)
- `admin_email` (por defecto `admin`)
- `admin_password`

## 4) Orden recomendado de ejecucion

- `Portal Auth / Login (Admin/Cliente)`
- `Portal Auth / Me (JWT)`
- `Admin Portal API / List Tenants`
- `DGII ENFC / Semilla (GET)`

Nota: la request `Validacion Certificado (XML firmado => token)` requiere que envies un XML realmente firmado. En ambiente local puedes omitirla si no tienes el XML firmado a mano.
