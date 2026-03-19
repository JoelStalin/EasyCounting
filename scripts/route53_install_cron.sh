#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="${SCRIPT_PATH:-/path/to/scripts/route53_update.sh}"
CRON_EXPR="${CRON_EXPR:-*/7 * * * *}"
CRON_LINE="$CRON_EXPR /bin/bash $SCRIPT_PATH >> $HOME/route53_dns_updates.log 2>&1"

( crontab -l 2>/dev/null | grep -v "route53_update.sh" || true; echo "$CRON_LINE" ) | crontab -

sudo service cron start

echo "Cron instalado: $CRON_LINE"
crontab -l
