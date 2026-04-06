# Repository Guidelines

## Project Structure & Module Organization
Application code lives in `app/` and follows a layered layout: `domain/` for core entities and enums, `application/` for services and ports, `infrastructure/` for SQLAlchemy, Alembic bootstrap, and repository adapters, and `presentation/` for FastAPI routes and middleware. Tests live in `tests/`, migrations in `alembic/`, and observability plus edge routing provisioning in `ops/` (`nginx/`, `prometheus/`, `loki/`, `promtail/`, `grafana/`).
Deployment automation lives in `.github/workflows/`. Runtime TLS helpers live in `scripts/` and `ops/certbot/`.

## Build, Test, and Development Commands
Use Docker Compose as the primary runtime:
- `docker compose up -d --build` builds and starts API, Postgres, Prometheus, Loki, Promtail, Grafana, and `nginx`.
- `docker compose logs -f api` tails application logs.
- `docker compose exec -T api python -m compileall -q app tests alembic` performs a quick syntax check inside the service container.
- `docker compose down -v` stops the stack and removes volumes.
- `sh scripts/renew_tls.sh --dry-run --no-random-sleep-on-renew` validates the DuckDNS-backed Let’s Encrypt renewal flow on the VPS.
- GitHub Actions deploys by SSH-ing into the VPS, syncing `.env` from `VPS_APP_ENV_FILE` (either raw file contents or a VPS path), syncing `main` into the checkout directory, and running `docker compose up -d --build --remove-orphans`.

Public API traffic is routed through `nginx` on `80/443`; the production entrypoint is `https://my-emr.duckdns.org`, and Grafana is served under `/grafana/`. Prometheus remains on `9090`, and Loki on `3100`.

## Coding Style & Naming Conventions
Target Python 3.11+. Use 4-space indentation, type hints on public functions, `snake_case` for modules/functions, and `PascalCase` for classes. Keep HTTP concerns in `presentation`, orchestration in `application`, and persistence in `infrastructure`. Prefer explicit service methods over fat route handlers.

## Testing Guidelines
Write tests first. Integration coverage lives in `tests/integration/` and should cover RBAC, patient access rules, and doctor workflows. Name test files `test_<feature>.py`. For endpoint behavior, prefer API-level tests over isolated mocks when the scenario crosses layers.

## Commit & Pull Request Guidelines
Use short imperative commits such as `Add patient assignment service` or `Wire Grafana provisioning`. PRs should summarize behavior changes, list validation commands, and mention schema, Docker, or observability changes explicitly. Include screenshots when dashboard or API contract changes affect operators.

## Security & Configuration Tips
Never store secrets outside controlled defaults. Override `JWT_SECRET_KEY`, admin credentials, database settings, and DuckDNS settings through environment variables. CI/CD syncs `.env` on the VPS from the `VPS_APP_ENV_FILE` environment secret, which may hold either raw env contents or a VPS file path, and `/var/log/emr/app.log`, `logs/`, `ops/letsencrypt/`, and `ops/acme-webroot/` should stay out of source control. GitHub Actions deploy requires `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_DEPLOY_PATH`, and `VPS_APP_ENV_FILE`; missing secrets fail the job before SSH setup.
