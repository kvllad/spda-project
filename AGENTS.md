# Repository Guidelines

## Project Structure & Module Organization
Application code lives in `app/` and follows a layered layout: `domain/` for core entities and enums, `application/` for services and ports, `infrastructure/` for SQLAlchemy, Alembic bootstrap, and repository adapters, and `presentation/` for FastAPI routes and middleware. Tests live in `tests/`, migrations in `alembic/`, and observability plus edge routing provisioning in `ops/` (`nginx/`, `prometheus/`, `loki/`, `promtail/`, `grafana/`).
Deployment automation lives in `.github/workflows/`, and remote rollout helpers live in `scripts/`.

## Build, Test, and Development Commands
Use Docker Compose as the primary runtime:
- `docker compose up -d --build` builds and starts API, Postgres, Prometheus, Loki, Promtail, and Grafana.
- `docker compose logs -f api` tails application logs.
- `docker compose exec -T api python -m compileall -q app tests alembic` performs a quick syntax check inside the service container.
- `docker compose down -v` stops the stack and removes volumes.
- `bash -n scripts/deploy_remote.sh` validates the VPS deploy helper.

Public API traffic is routed through `nginx` on port `80`; Grafana is exposed on `3000`, Prometheus on `9090`, and Loki on `3100`.

## Coding Style & Naming Conventions
Target Python 3.11+. Use 4-space indentation, type hints on public functions, `snake_case` for modules/functions, and `PascalCase` for classes. Keep HTTP concerns in `presentation`, orchestration in `application`, and persistence in `infrastructure`. Prefer explicit service methods over fat route handlers.

## Testing Guidelines
Write tests first. Integration coverage lives in `tests/integration/` and should cover RBAC, patient access rules, and doctor workflows. Name test files `test_<feature>.py`. For endpoint behavior, prefer API-level tests over isolated mocks when the scenario crosses layers.

## Commit & Pull Request Guidelines
Use short imperative commits such as `Add patient assignment service` or `Wire Grafana provisioning`. PRs should summarize behavior changes, list validation commands, and mention schema, Docker, or observability changes explicitly. Include screenshots when dashboard or API contract changes affect operators.

## Security & Configuration Tips
Never store secrets outside controlled defaults. Override `JWT_SECRET_KEY`, admin credentials, and database settings through environment variables. Keep `.env` local, and treat `/var/log/emr/app.log` as operational data rather than source-controlled output.
