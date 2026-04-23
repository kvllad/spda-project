#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-emr}"
APP_ENV_PATH="${APP_ENV_PATH:-${REPO_ROOT}/.env}"
IMAGE_TAG="${IMAGE_TAG:?IMAGE_TAG is required}"
DEPLOY_USER="${DEPLOY_USER:-${USER}}"
GITOPS_MIRROR_ROOT="${GITOPS_MIRROR_ROOT:-/home/${DEPLOY_USER}/gitops}"
GITOPS_MIRROR_PATH="${GITOPS_MIRROR_PATH:-${GITOPS_MIRROR_ROOT}/spda-project.git}"
FRONTEND_PATH="${REPO_ROOT}/spda-frontend"

if [[ ! -f "${APP_ENV_PATH}" ]]; then
  echo "Application env file not found: ${APP_ENV_PATH}" >&2
  exit 1
fi

if [[ ! -f "${FRONTEND_PATH}/package.json" ]]; then
  echo "Frontend sources are missing at ${FRONTEND_PATH}. Ensure git submodules are initialized." >&2
  exit 1
fi

export MINIKUBE_PROFILE
"${REPO_ROOT}/scripts/install_minikube.sh"
kubectl config use-context "${MINIKUBE_PROFILE}"

kubectl create namespace emr --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

kubectl -n emr create secret generic emr-runtime \
  --from-env-file="${APP_ENV_PATH}" \
  --dry-run=client \
  -o yaml | kubectl apply -f -

minikube image build -p "${MINIKUBE_PROFILE}" -t "emr-service-api:${IMAGE_TAG}" "${REPO_ROOT}"
minikube image build -p "${MINIKUBE_PROFILE}" -t "emr-service-frontend:${IMAGE_TAG}" "${FRONTEND_PATH}"

mkdir -p "${GITOPS_MIRROR_ROOT}"
if [[ ! -d "${GITOPS_MIRROR_PATH}" ]]; then
  git init --bare "${GITOPS_MIRROR_PATH}"
fi
snapshot_dir="$(mktemp -d)"
trap 'rm -rf "${snapshot_dir}"' EXIT
rsync -a \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.ruff_cache' \
  --exclude 'logs/letsencrypt' \
  --exclude 'ops/letsencrypt' \
  --exclude 'ops/acme-webroot' \
  "${REPO_ROOT}/" "${snapshot_dir}/"
git -C "${snapshot_dir}" init -b main
git -C "${snapshot_dir}" config user.name gitops-bootstrap
git -C "${snapshot_dir}" config user.email gitops@example.com
git -C "${snapshot_dir}" add .
git -C "${snapshot_dir}" commit -m "Update desired state to ${IMAGE_TAG}"
git -C "${snapshot_dir}" push --force "${GITOPS_MIRROR_PATH}" main:main

sudo tee /etc/systemd/system/emr-git-daemon.service >/dev/null <<EOF
[Unit]
Description=Git daemon for local Argo CD mirror
After=network.target

[Service]
Type=simple
User=${DEPLOY_USER}
WorkingDirectory=${GITOPS_MIRROR_ROOT}
ExecStart=/usr/bin/git daemon --verbose --export-all --reuseaddr --base-path=${GITOPS_MIRROR_ROOT} ${GITOPS_MIRROR_ROOT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now emr-git-daemon.service

if ! kubectl -n argocd get deployment argocd-server >/dev/null 2>&1; then
  kubectl apply --server-side -n argocd \
    -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
fi

kubectl apply -k "${REPO_ROOT}/ops/gitops/argocd"

if [[ -f "${REPO_ROOT}/ops/letsencrypt/live/my-emr.duckdns.org/fullchain.pem" ]]; then
  REPO_ROOT="${REPO_ROOT}" "${REPO_ROOT}/scripts/sync_k8s_tls_secret.sh"
fi

kubectl -n argocd rollout status deploy/argocd-server --timeout=600s
kubectl -n argocd rollout restart deploy/argocd-server
kubectl -n argocd rollout status deploy/argocd-server --timeout=600s

kubectl -n argocd annotate application emr-prod argocd.argoproj.io/refresh=hard --overwrite

for _ in $(seq 1 90); do
  status="$(kubectl -n argocd get application emr-prod -o jsonpath='{.status.sync.status}:{.status.health.status}' 2>/dev/null || true)"
  if [[ "${status}" == "Synced:Healthy" ]]; then
    exit 0
  fi
  sleep 10
done

kubectl -n argocd get application emr-prod -o yaml >&2 || true
kubectl -n emr get pods >&2 || true
exit 1
