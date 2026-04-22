#!/usr/bin/env bash
set -euo pipefail

MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-emr}"
MINIKUBE_CPUS="${MINIKUBE_CPUS:-2}"
MINIKUBE_MEMORY="${MINIKUBE_MEMORY:-2200}"
DEPLOY_USER="${DEPLOY_USER:-${USER}}"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_command curl
require_command docker
require_command sudo

sudo -n true >/dev/null 2>&1 || {
  echo "Passwordless sudo is required to bootstrap minikube on the VPS." >&2
  exit 1
}

sudo apt-get update
sudo apt-get install -y conntrack socat curl ca-certificates

if ! command -v kubectl >/dev/null 2>&1; then
  curl -fsSLo /tmp/kubectl \
    "https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
  sudo install -o root -g root -m 0755 /tmp/kubectl /usr/local/bin/kubectl
fi

if ! command -v minikube >/dev/null 2>&1; then
  curl -fsSLo /tmp/minikube \
    https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
  sudo install -o root -g root -m 0755 /tmp/minikube /usr/local/bin/minikube
fi

mkdir -p "${HOME}/.kube" "${HOME}/.minikube"

minikube start \
  --profile "${MINIKUBE_PROFILE}" \
  --driver=docker \
  --container-runtime=containerd \
  --cpus="${MINIKUBE_CPUS}" \
  --memory="${MINIKUBE_MEMORY}" \
  --addons=ingress \
  --addons=metrics-server \
  --wait=apiserver,system_pods,default_sa,node_ready

kubectl config use-context "${MINIKUBE_PROFILE}"

minikube_ip="$(minikube ip -p "${MINIKUBE_PROFILE}")"
http_node_port="$(kubectl -n ingress-nginx get service ingress-nginx-controller -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}')"
https_node_port="$(kubectl -n ingress-nginx get service ingress-nginx-controller -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')"

sudo tee /etc/systemd/system/minikube-${MINIKUBE_PROFILE}.service >/dev/null <<EOF
[Unit]
Description=Minikube cluster ${MINIKUBE_PROFILE}
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
Environment=HOME=/home/${DEPLOY_USER}
Environment=KUBECONFIG=/home/${DEPLOY_USER}/.kube/config
ExecStart=/usr/sbin/runuser -l ${DEPLOY_USER} -c '/usr/local/bin/minikube start --profile ${MINIKUBE_PROFILE} --driver=docker --container-runtime=containerd --cpus=${MINIKUBE_CPUS} --memory=${MINIKUBE_MEMORY} --addons=ingress --addons=metrics-server --wait=apiserver,system_pods,default_sa,node_ready'
ExecStop=/usr/sbin/runuser -l ${DEPLOY_USER} -c '/usr/local/bin/minikube stop --profile ${MINIKUBE_PROFILE}'
TimeoutStartSec=900

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/emr-ingress-http.service >/dev/null <<EOF
[Unit]
Description=Forward host port 80 to minikube ingress HTTP
After=minikube-${MINIKUBE_PROFILE}.service
Requires=minikube-${MINIKUBE_PROFILE}.service

[Service]
Type=simple
ExecStart=/usr/bin/socat TCP-LISTEN:80,fork,reuseaddr TCP:${minikube_ip}:${http_node_port}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/emr-ingress-https.service >/dev/null <<EOF
[Unit]
Description=Forward host port 443 to minikube ingress HTTPS
After=minikube-${MINIKUBE_PROFILE}.service
Requires=minikube-${MINIKUBE_PROFILE}.service

[Service]
Type=simple
ExecStart=/usr/bin/socat TCP-LISTEN:443,fork,reuseaddr TCP:${minikube_ip}:${https_node_port}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "minikube-${MINIKUBE_PROFILE}.service"
sudo systemctl disable --now "minikube-${MINIKUBE_PROFILE}-tunnel.service" 2>/dev/null || true
sudo rm -f "/etc/systemd/system/minikube-${MINIKUBE_PROFILE}-tunnel.service"
sudo systemctl daemon-reload
sudo systemctl enable --now emr-ingress-http.service
sudo systemctl enable --now emr-ingress-https.service
