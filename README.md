# EMR Service

Production-ready electronic medical record backend built with FastAPI, PostgreSQL, Alembic, Prometheus, Loki, and Grafana.

The repository now supports two runtime modes:

- local development through `docker compose`
- VPS deployment through `minikube` plus Argo CD GitOps

## Public Endpoints

- Frontend: `https://my-emr.duckdns.org/`
- API docs: `https://my-emr.duckdns.org/docs`
- ReDoc: `https://my-emr.duckdns.org/redoc`
- OpenAPI: `https://my-emr.duckdns.org/openapi.json`
- Health: `https://my-emr.duckdns.org/healthz`
- Grafana: `https://my-emr.duckdns.org/grafana/`
- Argo CD: `https://my-emr.duckdns.org/argocd/`

## Production Access

- API admin login: `admin`
- API admin password: `EfL/axcFq0Pb1I643MXtugej`
- Grafana login: `admin`
- Grafana password: `3hRW1LXS1G1WZmr8OG3gydNp`
- Argo CD login: `admin`
- Argo CD password: `jYs7EcTd6NebGZqB`

## Local Development

```bash
docker compose up -d --build
docker compose logs -f api
docker compose down -v
```

Useful checks:

```bash
./.venv/bin/ruff check .
./.venv/bin/pytest -q
docker compose exec -T api python -m compileall -q app tests alembic
```

## Authentication and Core Flows

Get an admin token:

```bash
curl -X POST https://my-emr.duckdns.org/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"YOUR_ADMIN_PASSWORD"}'
```

Create a doctor:

```bash
curl -X POST https://my-emr.duckdns.org/api/v1/admin/doctors \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"full_name":"Dr. Alice Smith","specialization":"Therapist","phone":"+79990000001","email":"doctor.alice@example.com","username":"doctor_alice","password":"DoctorPass123"}'
```

Create a patient:

```bash
curl -X POST https://my-emr.duckdns.org/api/v1/admin/patients \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"full_name":"Ivan Petrov","date_of_birth":"1990-01-10","gender":"male","phone":"+78880000001","email":"ivan.petrov@example.com","address":"Lenina 10","insurance_number":"POLICY-001","username":"patient_ivan","password":"PatientPass123"}'
```

Doctor login uses the same `/api/v1/auth/login` endpoint with doctor `username/password`. Patient login works identically.

Doctor actions:

- `GET /api/v1/doctors/me/patients`
- `GET /api/v1/doctors/me/patients/available`
- `POST /api/v1/doctors/me/patients/{patient_id}/assign`
- `GET /api/v1/doctors/me/patients/{patient_id}`
- `POST /api/v1/doctors/me/patients/{patient_id}/medical-records`
- `POST /api/v1/doctors/me/patients/{patient_id}/prescriptions`

Patient actions:

- `GET /api/v1/patients/me`
- `PATCH /api/v1/patients/me`

## GitOps Deployment

Desired state lives in:

- Kubernetes manifests: `ops/k8s/base/`
- production overlay: `ops/k8s/overlays/prod/`
- Argo CD resources: `ops/gitops/argocd/`

Pipeline behavior on `main`:

1. run `ruff` and `pytest`
2. run frontend build in `spda-frontend`
3. update `ops/k8s/overlays/prod/kustomization.yaml` with `sha-<commit>` for API and frontend images
4. SSH to the VPS, sync `.env`, build API and frontend images directly into `minikube`, refresh the local Git mirror consumed by Argo CD, and let Argo CD reconcile
5. run `scripts/e2e_remote.sh` against the public domain (including frontend homepage check)

Required GitHub environment secrets in `PROD`:

- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_KEY`
- `VPS_DEPLOY_PATH`
- `VPS_APP_ENV_FILE`

`VPS_APP_ENV_FILE` may contain raw `.env` contents or a path on the VPS.

## VPS Bootstrap and TLS

Manual VPS commands:

```bash
bash scripts/install_minikube.sh
bash scripts/bootstrap_cluster.sh
bash scripts/e2e_remote.sh
```

DuckDNS-backed Let's Encrypt renewal remains host-side:

```bash
sh scripts/renew_tls.sh --dry-run --no-random-sleep-on-renew
```

After renewal, `scripts/sync_k8s_tls_secret.sh` updates the `emr-tls` secret in both `emr` and `argocd` namespaces.
