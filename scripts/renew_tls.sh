#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

duckdns_domain="$(grep '^DUCKDNS_DOMAIN=' .env | cut -d= -f2-)"
duckdns_token="$(grep '^DUCKDNS_TOKEN=' .env | cut -d= -f2-)"

export DUCKDNS_DOMAIN="$duckdns_domain"
export DUCKDNS_TOKEN="$duckdns_token"

sudo -E certbot renew \
  --manual \
  --preferred-challenges dns \
  --manual-public-ip-logging-ok \
  --manual-auth-hook "$(pwd)/ops/certbot/duckdns-auth.sh" \
  --manual-cleanup-hook "$(pwd)/ops/certbot/duckdns-cleanup.sh" \
  --config-dir "$(pwd)/ops/letsencrypt" \
  --work-dir "$(pwd)/ops/letsencrypt/work" \
  --logs-dir "$(pwd)/logs/letsencrypt" \
  "$@"

docker compose exec -T nginx nginx -s reload
