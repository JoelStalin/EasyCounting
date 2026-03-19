#!/usr/bin/env bash
set -euo pipefail

AWS_PROFILE="${AWS_PROFILE:-dev01}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ZONE_NAME="${ZONE_NAME:-getupsoft.com.do.}"
TTL="${TTL:-300}"
LOG_FILE="${LOG_FILE:-$HOME/route53_dns_updates.log}"
TARGET_IP="${TARGET_IP:-}"

RECORDS_DEFAULT=(
  "dgii.getupsoft.com.do."
  "*.dgii.getupsoft.com.do."
  "dgiicliente.getupsoft.com.do."
  "*.dgiicliente.getupsoft.com.do."
  "dgiiadmin.getupsoft.com.do."
  "*.dgiiadmin.getupsoft.com.do."
)

if [ -n "${RECORDS_CSV:-}" ]; then
  IFS=',' read -r -a RECORDS <<< "${RECORDS_CSV}"
else
  RECORDS=("${RECORDS_DEFAULT[@]}")
fi

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

if [ -z "$TARGET_IP" ]; then
  TARGET_IP="$(curl -s http://checkip.amazonaws.com | tr -d '[:space:]')"
fi

if ! [[ "$TARGET_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  log "IP invalida: $TARGET_IP"
  exit 1
fi

ZONE_ID="$(aws route53 list-hosted-zones-by-name \
  --dns-name "$ZONE_NAME" \
  --query "HostedZones[?Name=='$ZONE_NAME'].Id | [0]" \
  --output text \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION")"

if [ -z "$ZONE_ID" ] || [ "$ZONE_ID" = "None" ]; then
  log "Hosted Zone no encontrada para $ZONE_NAME"
  exit 1
fi

ZONE_ID="${ZONE_ID#/hostedzone/}"
log "Hosted Zone ID: $ZONE_ID"
log "IP publica actual: $TARGET_IP"

for RECORD in "${RECORDS[@]}"; do
  CURRENT_IP="$(aws route53 list-resource-record-sets \
    --hosted-zone-id "$ZONE_ID" \
    --query "ResourceRecordSets[?Name=='$RECORD' && Type=='A'].ResourceRecords[0].Value" \
    --output text \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION" || true)"

  if [ "$CURRENT_IP" = "$TARGET_IP" ]; then
    log "Sin cambios: $RECORD ya apunta a $TARGET_IP"
    continue
  fi

  CHANGE_BATCH=$(cat <<EOF
{"Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"$RECORD","Type":"A","TTL":$TTL,"ResourceRecords":[{"Value":"$TARGET_IP"}]}}]}
EOF
  )

  aws route53 change-resource-record-sets \
    --hosted-zone-id "$ZONE_ID" \
    --change-batch "$CHANGE_BATCH" \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION" >/tmp/route53_update.out

  log "Actualizado: $RECORD -> $TARGET_IP"
  log "AWS response: $(cat /tmp/route53_update.out | tr -d '\n')"

  command -v dig >/dev/null 2>&1 && dig +short "$RECORD" || true
  command -v nslookup >/dev/null 2>&1 && nslookup "$RECORD" || true
  log "Diagnostico completado para $RECORD"
  echo "---" >> "$LOG_FILE"
done

log "Proceso completado"
