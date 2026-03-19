#!/bin/bash
set -e

# Ir a la ruta del proyecto montada en WSL
cd /mnt/c/Users/yoeli/Documents/dgii_encf

CORPORATE_PORT=18085
ADMIN_PORT=18081
CLIENT_PORT=18082
SELLER_PORT=18084
APEX_PORT=18083
API_PORT=28080

CORPORATE_DIST="frontend/apps/corporate-portal/dist"
ADMIN_DIST="frontend/apps/admin-portal/dist"
CLIENT_DIST="frontend/apps/client-portal/dist"
SELLER_DIST="frontend/apps/seller-portal/dist"
SERVER_SCRIPT="scripts/automation/serve_spa.py"

echo "==== 1. Levantando Containers en Docker Desktop via WSL ===="
docker compose -f docker-compose.yml -f deploy/docker-compose.wsl-local.yml up -d

echo "==== 2. Sirviendo Portales con Python Nativo de Ubuntu ===="
# Matamos instancias previas limpiamente
pkill -f "serve_spa.py" || true

nohup python3 $SERVER_SCRIPT --host 0.0.0.0 --dir $CORPORATE_DIST --port $CORPORATE_PORT > /dev/null 2>&1 &
nohup python3 $SERVER_SCRIPT --host 0.0.0.0 --dir $ADMIN_DIST --port $ADMIN_PORT --runtime-api-base-url "https://admin.getupsoft.com.do" --proxy-api-base-url "http://127.0.0.1:$API_PORT" > /dev/null 2>&1 &
nohup python3 $SERVER_SCRIPT --host 0.0.0.0 --dir $CLIENT_DIST --port $CLIENT_PORT --runtime-api-base-url "https://cliente.getupsoft.com.do" --proxy-api-base-url "http://127.0.0.1:$API_PORT" > /dev/null 2>&1 &
nohup python3 $SERVER_SCRIPT --host 0.0.0.0 --dir $SELLER_DIST --port $SELLER_PORT --runtime-api-base-url "https://socios.getupsoft.com.do" --proxy-api-base-url "http://127.0.0.1:$API_PORT" > /dev/null 2>&1 &
nohup python3 $SERVER_SCRIPT --host 0.0.0.0 --port $APEX_PORT --redirect-target "https://www.getupsoft.com.do" > /dev/null 2>&1 &

echo "Todos los servicios Frontend fueron desplegados en modo Linux puro (0.0.0.0)."
echo "URLs operativas: Administrador(:$ADMIN_PORT) | Cliente(:$CLIENT_PORT) | Corporate(:$CORPORATE_PORT)"
