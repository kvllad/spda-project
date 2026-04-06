#!/bin/sh
set -eu

if [ -z "${DUCKDNS_TOKEN:-}" ] || [ -z "${DUCKDNS_DOMAIN:-}" ]; then
  echo "Missing required DuckDNS environment variables" >&2
  exit 1
fi

response="$(curl -fsS "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&clear=true&verbose=true")"
printf '%s\n' "$response"
printf '%s' "$response" | grep -q '^OK'
