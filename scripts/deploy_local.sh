#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/dgii_encf}"
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"

cd "$REPO_DIR"

git pull --ff-only

docker compose pull

docker compose up -d --build

docker compose exec -T web alembic upgrade head

curl -fsS "$HEALTH_URL" >/dev/null

echo "OK: $HEALTH_URL"
