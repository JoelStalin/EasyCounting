#!/usr/bin/env bash
set -euo pipefail

CERTBOT_IMAGE="certbot/certbot:latest"

docker run --rm \
  -v "$(pwd)/ops/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/ops/certbot/www:/var/www/certbot" \
  $CERTBOT_IMAGE renew

docker compose restart nginx

echo "Certificados renovados y nginx reiniciado"
