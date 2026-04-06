#!/bin/sh
set -eu

if [ -z "${DUCKDNS_TOKEN:-}" ] || [ -z "${CERTBOT_DOMAIN:-}" ]; then
  echo "Missing required DuckDNS or Certbot environment variables" >&2
  exit 1
fi

case "$CERTBOT_DOMAIN" in
  *.duckdns.org) duckdns_domain="${CERTBOT_DOMAIN%.duckdns.org}" ;;
  *)
    echo "Unsupported domain for DuckDNS hook: $CERTBOT_DOMAIN" >&2
    exit 1
    ;;
esac

response="$(curl -fsS "https://www.duckdns.org/update?domains=${duckdns_domain}&token=${DUCKDNS_TOKEN}&clear=true&verbose=true")"
printf '%s\n' "$response"
printf '%s' "$response" | grep -q '^OK'
