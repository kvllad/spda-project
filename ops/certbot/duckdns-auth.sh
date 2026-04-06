#!/bin/sh
set -eu

if [ -z "${DUCKDNS_TOKEN:-}" ] || [ -z "${DUCKDNS_DOMAIN:-}" ] || [ -z "${CERTBOT_VALIDATION:-}" ]; then
  echo "Missing required DuckDNS or Certbot environment variables" >&2
  exit 1
fi

response="$(curl -fsS "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&txt=${CERTBOT_VALIDATION}&verbose=true")"
printf '%s\n' "$response"
printf '%s' "$response" | grep -q '^OK'

# Give resolvers a moment to pick up the TXT update.
sleep 30
