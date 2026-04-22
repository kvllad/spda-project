#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

duckdns_token="$(grep '^DUCKDNS_TOKEN=' .env | cut -d= -f2-)"

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

if command -v kubectl >/dev/null 2>&1 && kubectl config current-context >/dev/null 2>&1; then
  REPO_ROOT="$(pwd)" ./scripts/sync_k8s_tls_secret.sh
elif docker compose ps nginx >/dev/null 2>&1; then
  docker compose exec -T nginx nginx -s reload
fi
