# Local Environment Audit - 2026-03-19

## WSL & Docker Host
- **WSL 2 Distributions**: `Ubuntu` (Running), `docker-desktop` (Running).
- Docker engine is fully active and serving multiple independent environments concurrently.

## Active Docker Containers

1. **Plataforma Principal (DGII e-CF)**
   - Backend API: `dgii_encf-web-1` (Up 4 hours, healthy)
   - Database: `dgii_encf-db-1` (Up 4 hours, healthy)
   - Redis: `dgii_encf-redis-1` (Up 4 hours)
   - Demo Env: `dgii_encf-web_demo-1` (Up 15 hours, healthy)
   - Reverse Proxy: `dgii_encf-nginx-1` (Up 21 hours)

2. **Laboratorios Odoo (Locales)**
   - Odoo 19 (Chefalitas Lab): `odoo19_chefalitas-odoo-1` & `odoo19_chefalitas-db-1`
   - Odoo 15 (GetUpSoft): `getupsoft_odoo15-odoo-1` & `getupsoft_odoo15-db-1` (Up 3 hours, healthy)

## Local Frontend Services (Node/React)
All critical portal ports are currently `LISTENING` and returning `200 OK`:
- `127.0.0.1:28080` -> FastAPI Backend Principal
- `127.0.0.1:18081` -> Admin Portal
- `127.0.0.1:18082` -> Client Portal
- `127.0.0.1:18084` -> Seller Portal
- `127.0.0.1:18085` -> Corporate Portal
- `0.0.0.0:19069`   -> Odoo 19 UI

## Infraestructura Adicional
- **cloudflared**: Ejecutándose silenciosamente en background (PID 20488), lo que significa que el equipo está enrutando activamente solicitudes externas hacia tus contenedores.
