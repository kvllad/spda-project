# Repository Guidelines

## Project Structure & Module Organization
Application code lives in `app/` and follows a layered layout: `domain/` for core entities and enums, `application/` for services and ports, `infrastructure/` for SQLAlchemy, Alembic bootstrap, and repository adapters, and `presentation/` for FastAPI routes and middleware. Tests live in `tests/`, migrations in `alembic/`, and observability assets in `ops/` (`prometheus/`, `loki/`, `promtail/`, `grafana/`). Kubernetes manifests live in `ops/k8s/`, and Argo CD GitOps resources live in `ops/gitops/argocd/`.
Deployment automation lives in `.github/workflows/`. VPS bootstrap, TLS sync, and smoke checks live in `scripts/`. `ops/nginx/` remains only for local Docker Compose compatibility.

## Build, Test, and Development Commands
Use Docker Compose for local development and Minikube for VPS runtime:
- `docker compose up -d --build` builds and starts API, Postgres, Prometheus, Loki, Promtail, Grafana, and `nginx`.
- `docker compose logs -f api` tails application logs.
- `docker compose exec -T api python -m compileall -q app tests alembic` performs a quick syntax check inside the service container.
- `docker compose down -v` stops the stack and removes volumes.
- `bash scripts/install_minikube.sh` installs `kubectl` and `minikube`, starts the `emr` profile, enables ingress, and configures systemd services on the VPS.
- `bash scripts/bootstrap_cluster.sh` creates runtime secrets, installs Argo CD, and applies the GitOps app definitions.
- `bash scripts/e2e_remote.sh` runs the remote smoke flow against the deployed domain.
- `sh scripts/renew_tls.sh --dry-run --no-random-sleep-on-renew` validates the DuckDNS-backed Let’s Encrypt renewal flow on the VPS.
- GitHub Actions runs lint and tests, updates `ops/k8s/overlays/prod/kustomization.yaml` with `sha-<commit>`, SSH-es into the VPS, syncs the checkout, builds the image straight into `minikube`, refreshes the local git mirror consumed by Argo CD, and then runs the external E2E smoke script.

Production traffic is exposed through the Minikube ingress controller on `80/443`; the production entrypoint is `https://my-emr.duckdns.org`, Grafana is served under `/grafana/`, and Argo CD is served under `/argocd/`.

## Coding Style & Naming Conventions
Target Python 3.11+. Use 4-space indentation, type hints on public functions, `snake_case` for modules/functions, and `PascalCase` for classes. Keep HTTP concerns in `presentation`, orchestration in `application`, and persistence in `infrastructure`. Prefer explicit service methods over fat route handlers.

## Testing Guidelines
Write tests first. Integration coverage lives in `tests/integration/` and should cover RBAC, patient access rules, and doctor workflows. Name test files `test_<feature>.py`. For endpoint behavior, prefer API-level tests over isolated mocks when the scenario crosses layers. Every infrastructure or feature change must finish with a real E2E smoke run against the deployed domain, not only local pytest coverage.

## Commit & Pull Request Guidelines
Use short imperative commits such as `Add patient assignment service` or `Wire Grafana provisioning`. PRs should summarize behavior changes, list validation commands, and mention schema, Docker, or observability changes explicitly. Include screenshots when dashboard or API contract changes affect operators.

## Security & Configuration Tips
Never store secrets outside controlled defaults. Override `JWT_SECRET_KEY`, admin credentials, database settings, Grafana credentials, and DuckDNS settings through environment variables. CI/CD syncs `.env` on the VPS from the `VPS_APP_ENV_FILE` environment secret, which may hold either raw env contents or a VPS path, then converts it into the `emr-runtime` Kubernetes secret. GitHub Actions deploy requires `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_DEPLOY_PATH`, and `VPS_APP_ENV_FILE`; missing secrets fail the job before SSH setup.
