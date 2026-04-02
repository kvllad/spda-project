#!/bin/sh
set -eu

: "${DEPLOY_ROOT:?DEPLOY_ROOT is required}"
: "${RELEASE_SHA:?RELEASE_SHA is required}"
: "${ARCHIVE_NAME:?ARCHIVE_NAME is required}"

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-emr-service}"
KEEP_RELEASES="${KEEP_RELEASES:-5}"
RELEASES_DIR="${DEPLOY_ROOT}/releases"
SHARED_DIR="${DEPLOY_ROOT}/shared"
CURRENT_LINK="${DEPLOY_ROOT}/current"
RELEASE_DIR="${RELEASES_DIR}/${RELEASE_SHA}"
ARCHIVE_PATH="${DEPLOY_ROOT}/${ARCHIVE_NAME}"
ENV_PATH="${SHARED_DIR}/.env"

mkdir -p "${RELEASES_DIR}" "${SHARED_DIR}" "${RELEASE_DIR}"

if [ ! -f "${ENV_PATH}" ]; then
  echo "Missing shared env file at ${ENV_PATH}" >&2
  exit 1
fi

tar -xzf "${ARCHIVE_PATH}" -C "${RELEASE_DIR}"
cp "${ENV_PATH}" "${RELEASE_DIR}/.env"
ln -sfn "${RELEASE_DIR}" "${CURRENT_LINK}"

cd "${CURRENT_LINK}"
docker compose -p "${COMPOSE_PROJECT_NAME}" up -d --build --remove-orphans

i=0
until curl -fsS http://127.0.0.1/healthz >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "${i}" -ge 30 ]; then
    echo "Application health check failed after deployment." >&2
    docker compose -p "${COMPOSE_PROJECT_NAME}" ps >&2 || true
    docker compose -p "${COMPOSE_PROJECT_NAME}" logs --tail=100 nginx >&2 || true
    docker compose -p "${COMPOSE_PROJECT_NAME}" logs --tail=100 api >&2 || true
    exit 1
  fi
  sleep 2
done

rm -f "${ARCHIVE_PATH}"

ls -1dt "${RELEASES_DIR}"/* 2>/dev/null | tail -n +"$((KEEP_RELEASES + 1))" | xargs -r rm -rf --
