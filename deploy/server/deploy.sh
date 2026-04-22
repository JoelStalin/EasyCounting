#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=/opt/EasyCounting
COMPOSE_FILE="$PROJECT_ROOT/deploy/server/docker-compose.server.yml"
ENV_FILE="$PROJECT_ROOT/.env.production"
LOG_FILE="$PROJECT_ROOT/deploy/server/deploy.log"
LOCK_FILE="$PROJECT_ROOT/deploy/server/deploy.lock"

exec >>"$LOG_FILE" 2>&1
exec 9>"$LOCK_FILE"
flock -n 9

echo "[$(date -Is)] starting deploy"
cd "$PROJECT_ROOT"

git fetch origin main
git checkout main
git pull --ff-only origin main

rm -rf "$PROJECT_ROOT/frontend/.pnpm-store"

docker run --rm \
  -e CI=true \
  -v "$PROJECT_ROOT:/repo" \
  node:20-bookworm \
  bash -lc "
    rm -rf /tmp/frontend &&
    mkdir -p /tmp/frontend &&
    cp -a /repo/frontend/. /tmp/frontend/ &&
    cd /tmp/frontend &&
    corepack enable &&
    pnpm install --no-frozen-lockfile &&
    pnpm --filter @getupsoft/admin-portal build &&
    pnpm --filter @getupsoft/client-portal build &&
    pnpm --filter @getupsoft/seller-portal build &&
    pnpm --filter @getupsoft/corporate-portal build &&
    rm -rf /repo/frontend/apps/admin-portal/dist \
      /repo/frontend/apps/client-portal/dist \
      /repo/frontend/apps/seller-portal/dist \
      /repo/frontend/apps/corporate-portal/dist &&
    cp -a /tmp/frontend/apps/admin-portal/dist /repo/frontend/apps/admin-portal/dist &&
    cp -a /tmp/frontend/apps/client-portal/dist /repo/frontend/apps/client-portal/dist &&
    cp -a /tmp/frontend/apps/seller-portal/dist /repo/frontend/apps/seller-portal/dist &&
    cp -a /tmp/frontend/apps/corporate-portal/dist /repo/frontend/apps/corporate-portal/dist
  "

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" pull mailpit db redis || true
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build --remove-orphans
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T web alembic upgrade head

for _ in $(seq 1 40); do
  if curl -fsS http://127.0.0.1/healthz >/dev/null && curl -fsS http://127.0.0.1/readyz >/dev/null; then
    echo "[$(date -Is)] deploy ok"
    exit 0
  fi
  sleep 5
done

echo "[$(date -Is)] health checks failed"
exit 1
