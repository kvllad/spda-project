#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
DOMAIN="${DOMAIN:-my-emr.duckdns.org}"
TLS_SECRET_NAME="${TLS_SECRET_NAME:-emr-tls}"
CERT_DIR="${CERT_DIR:-${REPO_ROOT}/ops/letsencrypt/live/${DOMAIN}}"

FULLCHAIN="${CERT_DIR}/fullchain.pem"
PRIVKEY="${CERT_DIR}/privkey.pem"

file_exists() {
  local source_path="$1"

  if [[ -f "${source_path}" ]]; then
    return 0
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo test -f "${source_path}"
    return $?
  fi

  return 1
}

if ! file_exists "${FULLCHAIN}" || ! file_exists "${PRIVKEY}"; then
  echo "TLS certificate files not found in ${CERT_DIR}" >&2
  exit 1
fi

temp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "${temp_dir}"
}
trap cleanup EXIT

read_cert_file() {
  local source_path="$1"
  local target_path="$2"

  if [[ -r "${source_path}" ]]; then
    cp "${source_path}" "${target_path}"
    return 0
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo cat "${source_path}" > "${target_path}"
    return 0
  fi

  echo "Certificate file is not readable and sudo is unavailable: ${source_path}" >&2
  exit 1
}

fullchain_copy="${temp_dir}/fullchain.pem"
privkey_copy="${temp_dir}/privkey.pem"
read_cert_file "${FULLCHAIN}" "${fullchain_copy}"
read_cert_file "${PRIVKEY}" "${privkey_copy}"

for namespace in emr argocd; do
  kubectl create namespace "${namespace}" --dry-run=client -o yaml | kubectl apply -f -
  kubectl -n "${namespace}" create secret tls "${TLS_SECRET_NAME}" \
    --cert="${fullchain_copy}" \
    --key="${privkey_copy}" \
    --dry-run=client \
    -o yaml | kubectl apply -f -
done
