#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

domain="${1:-}"
if [ -z "$domain" ]; then
  echo "Usage: $0 <domain>" >&2
  exit 1
fi

duckdns_token="$(grep '^DUCKDNS_TOKEN=' .env | cut -d= -f2-)"

export DUCKDNS_TOKEN="$duckdns_token"

sudo -E certbot certonly \
  --manual \
  --preferred-challenges dns \
  --manual-public-ip-logging-ok \
  --manual-auth-hook "$(pwd)/ops/certbot/duckdns-auth.sh" \
  --manual-cleanup-hook "$(pwd)/ops/certbot/duckdns-cleanup.sh" \
  --config-dir "$(pwd)/ops/letsencrypt" \
  --work-dir "$(pwd)/ops/letsencrypt/work" \
  --logs-dir "$(pwd)/logs/letsencrypt" \
  --non-interactive \
  --agree-tos \
  --register-unsafely-without-email \
  -d "$domain"
