#!/usr/bin/env bash
set -euo pipefail

LE_EMAIL="${LE_EMAIL:-}"
if [ -z "$LE_EMAIL" ]; then
  echo "LE_EMAIL is required (e.g. LE_EMAIL=admin@getupsoft.com.do)"
  exit 1
fi

DOMAINS=(
  "dgii.getupsoft.com.do"
  "dgiicliente.getupsoft.com.do"
  "dgiiadmin.getupsoft.com.do"
)

CERTBOT_IMAGE="certbot/certbot:latest"

mkdir -p ops/certbot/www ops/certbot/conf

DOMAIN_ARGS=()
for d in "${DOMAINS[@]}"; do
  DOMAIN_ARGS+=("-d" "$d")
done

docker run --rm \
  -v "$(pwd)/ops/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/ops/certbot/www:/var/www/certbot" \
  $CERTBOT_IMAGE certonly --webroot \
  -w /var/www/certbot \
  --email "$LE_EMAIL" \
  --agree-tos \
  --no-eff-email \
  "${DOMAIN_ARGS[@]}"

echo "Certificados listos en ops/certbot/conf/live/dgii.getupsoft.com.do"
